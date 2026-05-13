from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.utils import timezone

from .forms import (
    ManualLeadForm, MarketOrderForm, MarketOrderRateForm,
    MarketOrderAssignForm, MarketOrderDOForm, QuotationEditForm, LineItemFormSet,
)
from database.models import Broker, Customer
from .models import Lead, MarketOrder, Quotation, QuotationLineItem
from .services.llm import generate_quotation_draft


@login_required
def lead_list(request):
    leads = Lead.objects.select_related('created_by').all()
    return render(request, 'quotations/lead_list.html', {'leads': leads})


@login_required
def lead_create(request):
    if request.method == 'POST':
        form = ManualLeadForm(request.POST)
        if form.is_valid():
            lead = form.save(commit=False)
            lead.source = 'manual'
            lead.created_by = request.user
            lead.save()
            messages.success(request, f'Lead #{lead.pk} created.')
            return redirect('lead_detail', pk=lead.pk)
    else:
        form = ManualLeadForm()
    return render(request, 'quotations/lead_create.html', {'form': form})


@login_required
def lead_detail(request, pk):
    lead = get_object_or_404(Lead.objects.prefetch_related('quotations'), pk=pk)
    return render(request, 'quotations/lead_detail.html', {'lead': lead})


@login_required
def quotation_list(request):
    quotations = Quotation.objects.select_related('lead', 'created_by').all()
    unquoted_leads = Lead.objects.filter(quotations__isnull=True)
    return render(request, 'quotations/quotation_list.html', {'quotations': quotations, 'unquoted_leads': unquoted_leads})


@login_required
def quotation_detail(request, pk):
    quotation = get_object_or_404(
        Quotation.objects.select_related('lead', 'created_by', 'approved_by').prefetch_related('line_items'),
        pk=pk,
    )
    return render(request, 'quotations/quotation_detail.html', _quotation_context(quotation))


@login_required
def quotation_edit(request, pk):
    quotation = get_object_or_404(Quotation, pk=pk)
    lead = quotation.lead

    if request.method == 'POST':
        form = QuotationEditForm(request.POST, instance=quotation)
        formset = LineItemFormSet(request.POST, instance=quotation)
        if form.is_valid() and formset.is_valid():
            form.save()
            items = formset.save(commit=False)
            for item in items:
                item.quantity = item.quantity or Decimal('0')
                item.unit_price = item.unit_price or Decimal('0')
                item.total_price = item.quantity * item.unit_price
                item.save()
            for item in formset.deleted_objects:
                item.delete()
            total = sum(i.total_price for i in quotation.line_items.all())
            quotation.total_amount = total
            quotation.save(update_fields=['total_amount'])
            _upsert_customer(lead, quotation.transport_extra)
            messages.success(request, 'Quotation saved.')
            return redirect('quotation_detail', pk=pk)
    else:
        initial = {}
        if quotation.transport_extra == 0 and lead.customer_name:
            customer = Customer.objects.filter(
                name__iexact=lead.customer_name,
                company__iexact=lead.company,
            ).first()
            if customer:
                initial['transport_extra'] = customer.transport_extra
        form = QuotationEditForm(instance=quotation, initial=initial)
        formset = LineItemFormSet(instance=quotation)

    return render(request, 'quotations/quotation_edit.html', {
        'quotation': quotation,
        'form': form,
        'formset': formset,
    })


def _upsert_customer(lead, transport_extra):
    if not lead.customer_name:
        return
    customer = Customer.objects.filter(
        name__iexact=lead.customer_name,
        company__iexact=lead.company,
    ).first()
    if customer:
        customer.transport_extra = transport_extra
        customer.phone = lead.customer_phone or customer.phone
        customer.email = lead.customer_email or customer.email
        customer.location = lead.location or customer.location
        customer.save()
    else:
        Customer.objects.create(
            name=lead.customer_name,
            company=lead.company,
            location=lead.location,
            phone=lead.customer_phone,
            email=lead.customer_email,
            transport_extra=transport_extra,
        )


def _quotation_context(quotation):
    items = list(quotation.line_items.all())
    total_tons = sum(i.quantity for i in items)
    item_value = sum(i.total_price for i in items)
    loading_extra = total_tons * Decimal('0.5')
    transport_extra = quotation.transport_extra
    taxable_value = item_value + loading_extra + transport_extra
    sgst = taxable_value * quotation.sgst_percent / 100
    cgst = taxable_value * quotation.cgst_percent / 100
    grand_total = taxable_value + sgst + cgst

    root = quotation.parent_quotation or quotation
    versions = Quotation.objects.filter(
        Q(pk=root.pk) | Q(parent_quotation=root)
    ).select_related('created_by').order_by('version')

    return {
        'quotation': quotation,
        'items': items,
        'total_tons': total_tons,
        'item_value': item_value,
        'loading_extra': loading_extra,
        'transport_extra': transport_extra,
        'taxable_value': taxable_value,
        'sgst': sgst,
        'cgst': cgst,
        'grand_total': grand_total,
        'versions': versions,
        'root': root,
    }


@login_required
def quotation_pdf(request, pk):
    quotation = get_object_or_404(
        Quotation.objects.select_related('lead', 'created_by').prefetch_related('line_items'),
        pk=pk,
    )
    ctx = _quotation_context(quotation)
    html = render_to_string('quotations/quotation_pdf.html', ctx, request=request)
    try:
        import weasyprint
        pdf = weasyprint.HTML(string=html, base_url=request.build_absolute_uri('/')).write_pdf()
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'filename="quotation_{quotation.quotation_number}.pdf"'
        return response
    except ImportError:
        return HttpResponse('WeasyPrint is not installed. Run: pip install weasyprint', status=500)


@login_required
def quotation_revise(request, pk):
    if request.method != 'POST':
        return redirect('quotation_detail', pk=pk)
    original = get_object_or_404(Quotation, pk=pk)
    root = original.parent_quotation or original
    next_version = Quotation.objects.filter(
        Q(pk=root.pk) | Q(parent_quotation=root)
    ).count() + 1
    new_q = Quotation.objects.create(
        lead=original.lead,
        parent_quotation=root,
        version=next_version,
        payment_terms=original.payment_terms,
        delivery_address=original.delivery_address,
        transport_extra=original.transport_extra,
        sgst_percent=original.sgst_percent,
        cgst_percent=original.cgst_percent,
        notes=original.notes,
        valid_until=original.valid_until,
        created_by=request.user,
    )
    for item in original.line_items.all():
        QuotationLineItem.objects.create(
            quotation=new_q,
            product_name=item.product_name,
            make=item.make,
            length=item.length,
            pcs=item.pcs,
            quantity=item.quantity,
            unit_price=item.unit_price,
            total_price=item.total_price,
            notes=item.notes,
        )
    messages.success(request, f'{new_q} created as a new revision.')
    return redirect('quotation_edit', pk=new_q.pk)


@login_required
def quotation_outcome(request, pk):
    if request.method != 'POST':
        return redirect('quotation_detail', pk=pk)
    quotation = get_object_or_404(Quotation, pk=pk)
    root = quotation.parent_quotation or quotation
    outcome = request.POST.get('outcome')
    if outcome in ('win', 'loss', 'not_updated'):
        root.outcome = outcome
        root.save(update_fields=['outcome'])
    return redirect('quotation_detail', pk=pk)


@login_required
def quotation_send(request, pk):
    if request.method != 'POST':
        return redirect('quotation_detail', pk=pk)
    quotation = get_object_or_404(Quotation, pk=pk)
    quotation.status = 'sent'
    quotation.sent_at = timezone.now()
    quotation.save(update_fields=['status', 'sent_at'])
    messages.success(request, f'{quotation} marked as sent.')
    return redirect('quotation_detail', pk=pk)


@login_required
def quotation_select_lead(request):
    leads = Lead.objects.select_related('created_by').order_by('-created_at')
    return render(request, 'quotations/quotation_select_lead.html', {'leads': leads})


@login_required
def quotation_create(request, lead_pk):
    lead = get_object_or_404(Lead, pk=lead_pk)
    if request.method == 'POST':
        quotation = Quotation.objects.create(
            lead=lead,
            created_by=request.user,
        )
        if lead.status == 'new':
            lead.status = 'processing'
            lead.save(update_fields=['status'])

        # Attempt LLM pre-fill; fall back silently if not yet wired
        try:
            if lead.broker:
                entity_notes = lead.broker.notes
            else:
                customer = Customer.objects.filter(
                    name__iexact=lead.customer_name,
                    company__iexact=lead.company,
                ).first()
                entity_notes = customer.notes if customer else ''

            draft = generate_quotation_draft(lead, entity_notes)
            quotation.llm_raw_response = str(draft)

            # Apply top-level fields from draft
            for field in ('payment_terms', 'delivery_address', 'transport_extra',
                          'sgst_percent', 'cgst_percent', 'notes', 'valid_until'):
                if draft.get(field) not in (None, ''):
                    setattr(quotation, field, draft[field])
            quotation.save()

            # Create line items from draft
            for item in draft.get('line_items', []):
                qty = Decimal(str(item.get('quantity') or 0))
                price = Decimal(str(item.get('unit_price') or 0))
                QuotationLineItem.objects.create(
                    quotation=quotation,
                    product_name=item.get('product_name', ''),
                    make=item.get('make', ''),
                    length=item.get('length'),
                    pcs=item.get('pcs'),
                    quantity=qty,
                    unit_price=price,
                    total_price=qty * price,
                    notes=item.get('notes', ''),
                )
        except (NotImplementedError, Exception):
            pass

        messages.success(request, f'{quotation} created as draft.')
        return redirect('quotation_edit', pk=quotation.pk)
    return redirect('quotation_select_lead')


@login_required
def quotation_approve(request, pk):
    if request.user.role not in ('lead', 'admin'):
        messages.error(request, 'Only team leads and admins can approve quotations.')
        return redirect('quotation_detail', pk=pk)

    quotation = get_object_or_404(Quotation, pk=pk, status='draft')
    if request.method == 'POST':
        quotation.status = 'approved'
        quotation.approved_by = request.user
        quotation.approved_at = timezone.now()
        quotation.save()
        messages.success(request, f'{quotation} approved.')
    return redirect('quotation_detail', pk=pk)


# ── Broker views ─────────────────────────────────────────────────────────────

def _require_market_or_admin(request):
    return request.user.team == 'market' or request.user.role == 'admin'




# ── Market Order views ────────────────────────────────────────────────────────

@login_required
def market_order_list(request):
    if not _require_market_or_admin(request):
        return redirect('dashboard')
    qs = MarketOrder.objects.select_related('broker', 'created_by', 'loading_dock_member')
    if request.user.role in ('primary', 'rolling'):
        qs = qs.filter(sub_team=request.user.role)
    elif request.user.role == 'loading_dock':
        qs = qs.filter(loading_dock_member=request.user)
    return render(request, 'quotations/market_order_list.html', {'orders': qs})


@login_required
def market_order_create(request):
    if not _require_market_or_admin(request):
        return redirect('dashboard')
    if request.method == 'POST':
        form = MarketOrderForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.created_by = request.user
            order.save()
            messages.success(request, f'{order} created.')
            return redirect('market_order_detail', pk=order.pk)
    else:
        form = MarketOrderForm()
    return render(request, 'quotations/market_order_create.html', {'form': form})


@login_required
def market_order_detail(request, pk):
    if not _require_market_or_admin(request):
        return redirect('dashboard')
    order = get_object_or_404(
        MarketOrder.objects.select_related('broker', 'created_by', 'loading_dock_member', 'quotation'),
        pk=pk,
    )
    rate_form = MarketOrderRateForm(instance=order) if order.status == 'new' else None
    assign_form = MarketOrderAssignForm(instance=order) if order.status == 'broker_confirmed' else None
    do_form = MarketOrderDOForm(instance=order) if order.status == 'do_pending' else None
    return render(request, 'quotations/market_order_detail.html', {
        'order': order,
        'rate_form': rate_form,
        'assign_form': assign_form,
        'do_form': do_form,
    })


@login_required
def market_order_set_rate(request, pk):
    if request.method != 'POST':
        return redirect('market_order_detail', pk=pk)
    order = get_object_or_404(MarketOrder, pk=pk, status='new')
    form = MarketOrderRateForm(request.POST, instance=order)
    if form.is_valid():
        order = form.save(commit=False)
        order.status = 'rate_sent'
        order.rate_sent_at = timezone.now()
        order.save()
        messages.success(request, 'Rate sent to broker.')
    return redirect('market_order_detail', pk=pk)


@login_required
def market_order_confirm(request, pk):
    if request.method != 'POST':
        return redirect('market_order_detail', pk=pk)
    order = get_object_or_404(MarketOrder, pk=pk, status='rate_sent')
    order.status = 'broker_confirmed'
    order.broker_confirmed_at = timezone.now()
    order.save(update_fields=['status', 'broker_confirmed_at'])
    messages.success(request, 'Broker confirmation recorded.')
    return redirect('market_order_detail', pk=pk)


@login_required
def market_order_assign_do(request, pk):
    if request.method != 'POST':
        return redirect('market_order_detail', pk=pk)
    if request.user.role not in ('lead', 'admin'):
        messages.error(request, 'Only team leads and admins can assign loading dock.')
        return redirect('market_order_detail', pk=pk)
    order = get_object_or_404(MarketOrder, pk=pk, status='broker_confirmed')
    form = MarketOrderAssignForm(request.POST, instance=order)
    if form.is_valid():
        order = form.save(commit=False)
        order.status = 'do_pending'
        order.do_requested_at = timezone.now()
        order.save()
        messages.success(request, 'Sent to loading dock.')
    return redirect('market_order_detail', pk=pk)


@login_required
def market_order_set_do(request, pk):
    if request.method != 'POST':
        return redirect('market_order_detail', pk=pk)
    order = get_object_or_404(MarketOrder, pk=pk, status='do_pending')
    if order.loading_dock_member != request.user and request.user.role != 'admin':
        messages.error(request, 'Only the assigned loading dock member can enter the DO number.')
        return redirect('market_order_detail', pk=pk)
    form = MarketOrderDOForm(request.POST, instance=order)
    if form.is_valid():
        order = form.save(commit=False)
        order.status = 'completed'
        order.do_issued_at = timezone.now()
        order.save()
        messages.success(request, f'DO number {order.do_number} recorded. Order completed.')
    return redirect('market_order_detail', pk=pk)
