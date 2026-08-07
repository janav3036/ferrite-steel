import io
import threading

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db import connection
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from aegis.models import CustomUser
from aegis.notifications import notify
from database.models import Customer
from .forms import CreditAssessmentRequestForm
from .models import CreditAssessment
from .services.crm_history import build_quotation_signal
from .services.extractor import extract_trading_history
from .services.llm import assess_credit, compute_data_confidence


def _run_assessment(assessment_id, file_bytes, filename, customer_id, notes, requested_by_id):
    """Runs on a background thread — Django gives each thread its own DB
    connection automatically, but nothing closes it when the thread ends
    (there's no request_finished signal here), so we must close it ourselves."""
    try:
        customer = Customer.objects.get(pk=customer_id)
        trading_history = extract_trading_history(io.BytesIO(file_bytes), filename, customer)
        quotation_signal = build_quotation_signal(customer)
        if quotation_signal:
            trading_history['quotation_signal'] = quotation_signal
        prior_assessment = CreditAssessment.objects.filter(
            customer=customer, status='done',
        ).order_by('-created_at').first()

        result = assess_credit(
            customer, notes, trading_history,
            prior_assessment=prior_assessment, quotation_signal=quotation_signal,
        )
        confidence = compute_data_confidence(trading_history, notes, quotation_signal)

        CreditAssessment.objects.filter(pk=assessment_id).update(
            trading_history=trading_history,
            score=result['score'], risk_level=result['risk_level'], data_confidence=confidence,
            recommendation=result['recommendation'], summary=result['summary'],
            factors=result['factors'], llm_raw_response=result['raw_response'],
            status='done',
        )
        customer.credit_status = result['risk_level']
        customer.last_assessed_at = timezone.now()
        customer.save(update_fields=['credit_status', 'last_assessed_at'])

        if result['risk_level'] == 'high':
            recipients = CustomUser.objects.filter(role__in=['lead', 'admin'], is_active=True).exclude(pk=requested_by_id)
            if customer.handling_team:
                recipients = recipients.filter(team=customer.handling_team) | CustomUser.objects.filter(role='admin', is_active=True)
            notify(
                recipients.distinct(), f'High credit risk: {customer.name}',
                message=f'{customer.name} scored {result["score"]}/10 (high risk) — '
                        f'recommendation: {result["recommendation"]}.',
                link=f'/credit-risk/{assessment_id}/', notif_type='credit_high_risk',
            )
    except Exception as e:
        CreditAssessment.objects.filter(pk=assessment_id).update(status='failed', error_message=str(e))
    finally:
        connection.close()


@login_required
def assessment_list(request):
    if request.user.role not in ('lead', 'admin'):
        messages.error(request, 'You do not have access to Credit Risk.')
        return redirect('dashboard')

    scope = request.GET.get('scope', 'team')
    risk_f = request.GET.get('risk_level', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')

    if scope == 'all' or request.user.role == 'admin':
        qs = CreditAssessment.objects.select_related('customer', 'requested_by').all()
    elif request.user.team:
        qs = CreditAssessment.objects.select_related('customer', 'requested_by').filter(
            customer__handling_team=request.user.team
        )
    else:
        qs = CreditAssessment.objects.none()

    if risk_f:
        qs = qs.filter(risk_level=risk_f)
    if date_from:
        qs = qs.filter(created_at__date__gte=date_from)
    if date_to:
        qs = qs.filter(created_at__date__lte=date_to)

    paginator = Paginator(qs, 25)
    page_obj = paginator.get_page(request.GET.get('page'))
    has_processing = any(a.status == 'processing' for a in page_obj)
    return render(request, 'credit_risk/assessment_list.html', {
        'page_obj': page_obj, 'scope': scope, 'risk_f': risk_f,
        'date_from': date_from, 'date_to': date_to,
        'risk_choices': CreditAssessment.RISK_LEVEL_CHOICES,
        'has_processing': has_processing,
    })

@login_required
def assessment_create(request):
    if request.user.role not in ('lead', 'admin'):
        messages.error(request, 'Only team leads and admins can run credit assessments.')
        return redirect('dashboard')

    preset_customer = None
    customer_pk = request.GET.get('customer') or request.POST.get('customer')
    if customer_pk:
        preset_customer = get_object_or_404(Customer, pk=customer_pk)

    if request.method == 'POST':
        form = CreditAssessmentRequestForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            customer = form.cleaned_data['customer']
            notes = form.cleaned_data['notes']
            file_obj = form.cleaned_data['trading_file']
            filename = file_obj.name
            file_bytes = file_obj.read()

            assessment = CreditAssessment.objects.create(
                customer=customer, requested_by=request.user, notes=notes,
                trading_history_source_filename=filename, status='processing',
            )
            threading.Thread(
                target=_run_assessment,
                args=(assessment.pk, file_bytes, filename, customer.pk, notes, request.user.pk),
                daemon=True,
            ).start()

            messages.success(request, f'Credit assessment for {customer.name} started — it will show as "Processing" until done.')
            return redirect('assessment_list')
    else:
        initial = {'customer': preset_customer} if preset_customer else {}
        form = CreditAssessmentRequestForm(user=request.user, initial=initial)

    return render(request, 'credit_risk/assessment_create.html', {
        'form': form, 'preset_customer': preset_customer,
    })


@login_required
def assessment_detail(request, pk):
    assessment = get_object_or_404(
        CreditAssessment.objects.select_related('customer', 'requested_by'), pk=pk
    )
    if request.user.role not in ('lead', 'admin'):
        messages.error(request, 'You do not have access to Credit Risk.')
        return redirect('dashboard')
    if request.user.role == 'lead' and request.user.team and assessment.customer.handling_team != request.user.team:
        messages.error(request, 'You do not have access to this assessment.')
        return redirect('assessment_list')
    prior_assessment = CreditAssessment.objects.filter(
        customer=assessment.customer, status='done', created_at__lt=assessment.created_at,
    ).order_by('-created_at').first()

    # Score medallion: an SVG ring drawn via stroke-dashoffset. Computed here
    # rather than in the template since Django templates can't do subtraction.
    ring_circumference = 314  # 2 * pi * r, r=50, rounded
    ring_offset = ring_circumference
    if assessment.score:
        ring_offset = round(ring_circumference * (1 - assessment.score / 10))

    return render(request, 'credit_risk/assessment_detail.html', {
        'assessment': assessment, 'prior_assessment': prior_assessment,
        'ring_circumference': ring_circumference, 'ring_offset': ring_offset,
    })


@login_required
def assessment_mark_failed(request, pk):
    assessment = get_object_or_404(CreditAssessment.objects.select_related('customer'), pk=pk)
    if request.user.role not in ('lead', 'admin'):
        messages.error(request, 'You do not have access to Credit Risk.')
        return redirect('dashboard')
    if request.user.role == 'lead' and request.user.team and assessment.customer.handling_team != request.user.team:
        messages.error(request, 'You do not have access to this assessment.')
        return redirect('assessment_list')

    if request.method == 'POST' and assessment.status == 'processing':
        assessment.status = 'failed'
        assessment.error_message = 'Manually marked as failed (stuck in processing).'
        assessment.save(update_fields=['status', 'error_message'])
        messages.success(request, 'Assessment marked as failed.')
    return redirect('assessment_detail', pk=assessment.pk)


@login_required
def assessment_delete(request, pk):
    assessment = get_object_or_404(CreditAssessment.objects.select_related('customer'), pk=pk)
    if request.user.role not in ('lead', 'admin'):
        messages.error(request, 'You do not have access to Credit Risk.')
        return redirect('dashboard')
    if request.user.role == 'lead' and request.user.team and assessment.customer.handling_team != request.user.team:
        messages.error(request, 'You do not have access to this assessment.')
        return redirect('assessment_list')

    if request.method == 'POST':
        customer = assessment.customer
        assessment.delete()
        # customer.credit_status/last_assessed_at are a cache of the most recent
        # assessment — if we just deleted that one, the cache is now stale and
        # must be recomputed from whatever's left (or cleared if nothing is).
        latest = CreditAssessment.objects.filter(customer=customer, status='done').order_by('-created_at').first()
        customer.credit_status = latest.risk_level if latest else ''
        customer.last_assessed_at = latest.created_at if latest else None
        customer.save(update_fields=['credit_status', 'last_assessed_at'])
        messages.success(request, 'Credit assessment deleted.')
        return redirect('customer_detail', pk=customer.pk)

    return render(request, 'credit_risk/assessment_confirm_delete.html', {'assessment': assessment})