from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone

from database.models import Customer
from .forms import CreditAssessmentRequestForm
from .models import CreditAssessment
from .services.extractor import extract_trading_history
from .services.llm import assess_credit


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
    return render(request, 'credit_risk/assessment_list.html', {
        'page_obj': page_obj, 'scope': scope, 'risk_f': risk_f,
        'date_from': date_from, 'date_to': date_to,
        'risk_choices': CreditAssessment.RISK_LEVEL_CHOICES,
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
            try:
                trading_history = extract_trading_history(file_obj, file_obj.name, customer)
                result = assess_credit(customer, notes, trading_history)
                assessment = CreditAssessment.objects.create(
                    customer=customer, requested_by=request.user, notes=notes,
                    trading_history=trading_history, trading_history_source_filename=file_obj.name,
                    score=result['score'], risk_level=result['risk_level'],
                    recommendation=result['recommendation'], summary=result['summary'],
                    factors=result['factors'], llm_raw_response=result['raw_response'],
                )
                customer.credit_status = assessment.risk_level
                customer.last_assessed_at = timezone.now()
                customer.save(update_fields=['credit_status', 'last_assessed_at'])
                messages.success(request, 'Credit assessment completed.')
                return redirect('assessment_detail', pk=assessment.pk)
            except Exception as e:
                messages.error(request, f'Assessment failed: {e}')
                return redirect(f"{reverse('assessment_create')}?customer={customer.pk}")
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
    return render(request, 'credit_risk/assessment_detail.html', {'assessment': assessment})