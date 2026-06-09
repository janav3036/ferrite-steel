import json
import re
from decimal import Decimal

from django.db import transaction
from django.db.models import F
from django.db.models.functions import Greatest

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.utils import timezone
from django.core.management import call_command
from django.views.decorators.http import require_POST


from .forms import (
    ManualLeadForm, MarketOrderForm, MarketOrderRateForm,
    MarketOrderAssignForm, MarketOrderDOForm, QuotationEditForm, LineItemFormSet,
)
from database.models import Customer, Product
from .models import Lead, MarketOrder, Quotation, QuotationLineItem, TeamEmailConfig
from .services.llm import generate_quotation_draft


@login_required
def lead_list(request):
    q = request.GET.get('q', '').strip()
    status_f = request.GET.get('status', '')
    source_f = request.GET.get('source', '')
    qs = Lead.objects.select_related('created_by').all()
    if q:
        qs = qs.filter(Q(company__icontains=q) | Q(customer_name__icontains=q) | Q(customer_email__icontains=q))
    if status_f:
        qs = qs.filter(status=status_f)
    if source_f:
        qs = qs.filter(source=source_f)
    params = request.GET.copy()
    params.pop('page', None)
    paginator = Paginator(qs, 25)
    page_obj = paginator.get_page(request.GET.get('page'))
    elided = [None if r == paginator.ELLIPSIS else r for r in paginator.get_elided_page_range(page_obj.number, on_each_side=2, on_ends=1)]
    return render(request, 'quotations/lead_list.html', {
        'page_obj': page_obj,
        'elided_page_range': elided,
        'q': q,
        'status_f': status_f,
        'source_f': source_f,
        'query_string': params.urlencode(),
        'lead_statuses': Lead.STATUS_CHOICES,
        'lead_sources': Lead.SOURCE_CHOICES,
    })


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
    from .models import ProductKeyword
    lead = get_object_or_404(Lead.objects.prefetch_related('quotations'), pk=pk)
    keywords = list(ProductKeyword.objects.filter(is_active=True).values('keyword', 'maps_to'))
    return render(request, 'quotations/lead_detail.html', {'lead': lead, 'voice_keywords': keywords})


@login_required
@require_POST
def lead_save_notes(request, pk):
    lead = get_object_or_404(Lead, pk=pk)
    action = request.POST.get('action')

    if action == 'save':
        lead.lead_notes_raw = request.POST.get('lead_notes_raw', '').strip()
        lead.save(update_fields=['lead_notes_raw'])
        messages.success(request, 'Notes saved.')

    elif action == 'cleanup':
        raw = request.POST.get('lead_notes_raw', '').strip()
        lead.lead_notes_raw = raw
        if raw:
            from .services.llm import cleanup_lead_notes
            lead.lead_notes_clean = cleanup_lead_notes(raw)
            messages.success(request, 'Notes cleaned up by AI.')
        else:
            messages.warning(request, 'No notes to clean up.')
        lead.save(update_fields=['lead_notes_raw', 'lead_notes_clean'])

    elif action == 'save_clean':
        lead.lead_notes_clean = request.POST.get('lead_notes_clean', '').strip()
        lead.save(update_fields=['lead_notes_clean'])
        messages.success(request, 'Cleaned notes saved.')

    return redirect('lead_detail', pk=pk)


@login_required
def quotation_list(request):
    q = request.GET.get('q', '').strip()
    status_f = request.GET.get('status', '')
    outcome_f = request.GET.get('outcome', '')
    qs = Quotation.objects.select_related('lead', 'created_by').all()
    if q:
        qs = qs.filter(Q(quotation_number__icontains=q) | Q(lead__company__icontains=q) | Q(lead__customer_name__icontains=q))
    if status_f:
        qs = qs.filter(status=status_f)
    if outcome_f:
        qs = qs.filter(outcome=outcome_f)
    params = request.GET.copy()
    params.pop('page', None)
    paginator = Paginator(qs, 25)
    page_obj = paginator.get_page(request.GET.get('page'))
    elided = [None if r == paginator.ELLIPSIS else r for r in paginator.get_elided_page_range(page_obj.number, on_each_side=2, on_ends=1)]
    unquoted_leads = Lead.objects.filter(quotations__isnull=True)
    return render(request, 'quotations/quotation_list.html', {
        'page_obj': page_obj,
        'elided_page_range': elided,
        'unquoted_leads': unquoted_leads,
        'q': q,
        'status_f': status_f,
        'outcome_f': outcome_f,
        'query_string': params.urlencode(),
        'quotation_statuses': Quotation.STATUS_CHOICES,
        'quotation_outcomes': Quotation.OUTCOME_CHOICES,
    })


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
    customer = _find_customer(lead)
    addon_notes = _parse_addon_notes(customer.notes if customer else '')

    if request.method == 'POST':
        form = QuotationEditForm(request.POST, instance=quotation)
        formset = LineItemFormSet(request.POST, instance=quotation)
        if form.is_valid() and formset.is_valid():
            form.save()
            items = formset.save(commit=False)
            for item in items:
                item.quantity = item.quantity or Decimal('0')
                item.unit_price = item.unit_price or Decimal('0')
                tons = item.quantity / Decimal('1000') if item.uom == 'kg' else item.quantity
                item.total_price = tons * item.unit_price
                item.save()
            for item in formset.deleted_objects:
                item.delete()
            total = sum(i.final_price for i in quotation.line_items.all())
            quotation.total_amount = total
            quotation.save(update_fields=['total_amount'])
            _upsert_customer(lead, quotation.transport_extra)
            _apply_catalog_rate_updates(request)
            messages.success(request, 'Quotation saved.')
            return redirect('quotation_detail', pk=pk)
    else:
        initial = {}
        if quotation.transport_extra == 0 and not lead.broker:
            if customer:
                initial['transport_extra'] = customer.transport_extra
        if not quotation.delivery_address and customer:
            initial['delivery_address'] = customer.shipping_address or customer.billing_address
        form = QuotationEditForm(instance=quotation, initial=initial)
        formset = LineItemFormSet(instance=quotation)

    addon_defaults_json = json.dumps({k: addon_notes.get(k, '') for k in _ADDON_KEYS})
    return render(request, 'quotations/quotation_edit.html', {
        'quotation': quotation,
        'lead': lead,
        'form': form,
        'formset': formset,
        'addon_defaults_json': addon_defaults_json,
        'customer_notes': customer.notes if customer else '',
    })


def _find_customer(lead):
    """Return matching Customer by email first, then name+company. None if not found."""
    if lead.customer_email:
        customer = Customer.objects.filter(email__iexact=lead.customer_email).first()
        if customer:
            return customer
    if lead.customer_name:
        return Customer.objects.filter(
            name__iexact=lead.customer_name,
            company__iexact=lead.company,
        ).first()
    return None


_ADDON_KEYS = ['parity', 'cutting', 'loading', 'transport', 'margin', 'interest', 'commission']
_ADDON_SECTION_RE = re.compile(r'---\s*Pricing Add-ons.*?---', re.DOTALL | re.IGNORECASE)


def _parse_addon_notes(notes: str) -> dict:
    """Extract last-used pricing add-on values from the structured section in customer notes."""
    match = _ADDON_SECTION_RE.search(notes or '')
    if not match:
        return {}
    section = match.group(0)
    result = {}
    for key in _ADDON_KEYS:
        m = re.search(rf'{key}\s*:\s*([^\n]+)', section, re.IGNORECASE)
        if m:
            result[key] = m.group(1).strip()
    return result


def _apply_catalog_rate_updates(request):
    """Update Product.rate (or rate_offset for derived products) from catalog_rate_update_* POST params."""
    for key in request.POST:
        if not key.startswith('catalog_rate_update_'):
            continue
        product_id = key[len('catalog_rate_update_'):]
        try:
            new_rate = Decimal(request.POST[key])
            p = Product.objects.select_related('base_product').get(pk=int(product_id))
            if p.base_product_id:
                p.rate_offset = new_rate - p.base_product.rate
                p.save(update_fields=['rate_offset'])
            else:
                p.rate = new_rate
                p.save(update_fields=['rate'])
        except (ValueError, Product.DoesNotExist):
            pass


def _upsert_customer(lead, transport_extra):
    if not lead.customer_name and not lead.customer_email:
        return
    customer = _find_customer(lead)
    if customer:
        customer.transport_extra = transport_extra
        customer.phone = lead.customer_phone or customer.phone
        customer.email = lead.customer_email or customer.email
        customer.billing_address = lead.location or customer.billing_address
        customer.save()
    else:
        Customer.objects.create(
            name=lead.customer_name,
            company=lead.company,
            billing_address=lead.location or '',
            phone=lead.customer_phone,
            email=lead.customer_email,
            transport_extra=transport_extra,
        )


def _quotation_context(quotation):
    items = list(quotation.line_items.all())
    total_tons = sum(i.quantity for i in items)
    item_value = sum(i.final_price for i in items)
    loading_extra = quotation.loading_extra
    transport_extra = quotation.transport_extra
    taxable_value = item_value + loading_extra + transport_extra
    sgst = taxable_value * quotation.sgst_percent / 100
    cgst = taxable_value * quotation.cgst_percent / 100
    grand_total = taxable_value + sgst + cgst

    root = Quotation.objects.select_related('winning_quotation').get(
        pk=(quotation.parent_quotation_id or quotation.pk)
    )
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
        loading_extra=original.loading_extra,
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
            product=item.product,
            product_name=item.product_name,
            make=item.make,
            length=item.length,
            hsn_code=item.hsn_code,
            pcs=item.pcs,
            quantity=item.quantity,
            uom=item.uom,
            unit_price=item.unit_price,
            total_price=item.total_price,
            discount_pct=item.discount_pct,
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
    if outcome in ('win', 'loss') and quotation.status != 'sent':
        messages.error(request, 'A quotation must be sent before it can be marked Won or Lost.')
        return redirect('quotation_detail', pk=pk)
    if outcome in ('win', 'loss', 'not_updated'):
        with transaction.atomic():
            root.outcome = outcome
            if outcome == 'win':
                root.winning_quotation = quotation
                if not root.stock_deducted:
                    _deduct_stock(quotation)
                    root.stock_deducted = True
            else:
                root.winning_quotation = None
            root.save(update_fields=['outcome', 'winning_quotation', 'stock_deducted'])
            lead = root.lead
            if outcome in ('win', 'loss') and lead.status != 'closed':
                lead.status = 'closed'
                lead.save(update_fields=['status'])
    return redirect('quotation_detail', pk=pk)


def _deduct_stock(quotation):
    for item in quotation.line_items.all():
        if not item.product_id:
            continue
        qty = item.quantity / Decimal('1000') if item.uom == 'kg' else item.quantity
        Product.objects.filter(pk=item.product_id).update(
            quantity=Greatest(F('quantity') - qty, Decimal('0'))
        )


def _send_via_smtp(config, to_email, subject, body, pdf_bytes=None, filename=None):
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.base import MIMEBase
    from email.mime.text import MIMEText
    from email import encoders

    smtp_host = config.smtp_host or config.imap_host.replace('imap.', 'smtp.')
    msg = MIMEMultipart()
    msg['From'] = config.email_address
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    if pdf_bytes and filename:
        part = MIMEBase('application', 'pdf')
        part.set_payload(pdf_bytes)
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename="{filename}"')
        msg.attach(part)

    if config.smtp_use_ssl:
        server = smtplib.SMTP_SSL(smtp_host, config.smtp_port)
    else:
        server = smtplib.SMTP(smtp_host, config.smtp_port)
        server.starttls()
    server.login(config.smtp_username or config.imap_username, config.smtp_password or config.imap_password)
    server.sendmail(config.email_address, [to_email], msg.as_string())
    server.quit()


@login_required
def quotation_send(request, pk):
    quotation = get_object_or_404(Quotation, pk=pk)
    lead = quotation.lead

    if request.method == 'POST':
        to_email = request.POST.get('to_email', '').strip()
        subject = request.POST.get('subject', '').strip()
        body = request.POST.get('body', '').strip()
        # Append a reference marker so poll_emails can recognise replies and skip them
        body_with_ref = body + f'\n\n[Quotation Reference: {quotation.quotation_number}]'

        sent_to = None
        if to_email:
            team = lead.created_by.team if lead.created_by else None
            config = (
                TeamEmailConfig.objects.filter(is_active=True, team=team).first()
                if team else None
            ) or TeamEmailConfig.objects.filter(is_active=True).first()

            if config:
                try:
                    pdf_bytes = None
                    filename = None
                    if not lead.broker:
                        import weasyprint
                        ctx = _quotation_context(quotation)
                        html = render_to_string('quotations/quotation_pdf.html', ctx, request=request)
                        pdf_bytes = weasyprint.HTML(
                            string=html, base_url=request.build_absolute_uri('/')
                        ).write_pdf()
                        filename = f"{quotation.quotation_number}.pdf"
                    _send_via_smtp(
                        config,
                        to_email=to_email,
                        subject=subject,
                        body=body_with_ref,
                        pdf_bytes=pdf_bytes,
                        filename=filename,
                    )
                    sent_to = to_email
                except Exception as exc:
                    messages.error(request, f'Email failed: {exc}')
                    return render(request, 'quotations/quotation_send_confirm.html', {
                        'quotation': quotation,
                        'to_email': to_email,
                        'subject': subject,
                        'body': body,
                    })
            else:
                messages.warning(request, 'No active team email config — marked as sent without emailing.')

        quotation.status = 'sent'
        quotation.sent_at = timezone.now()
        quotation.save(update_fields=['status', 'sent_at'])

        if sent_to:
            messages.success(request, f'{quotation} sent to {sent_to}.')
        else:
            messages.success(request, f'{quotation} marked as sent.')
        return redirect('quotation_detail', pk=pk)

    # GET — show confirmation form with pre-filled defaults
    if lead.broker:
        lines = quotation.line_items.all()
        rates_lines = '\n'.join(
            f"  {item.product_name}"
            + (f" ({item.make})" if item.make else "")
            + f": {item.quantity} T @ ₹{item.unit_price}/T"
            for item in lines
        )
        default_subject = f"Rates — {quotation.quotation_number}"
        default_body = (
            f"Hi {lead.customer_name or lead.broker.name},\n\n"
            f"Please find below our rates for your enquiry:\n\n"
            f"{rates_lines}\n\n"
            f"Payment Terms: {quotation.payment_terms}\n\n"
            f"Regards,\nFerrite Steel"
        )
        to_email = lead.customer_email or lead.broker.email
    else:
        default_subject = f"Quotation {quotation.quotation_number} — Ferrite Steel"
        default_body = (
            f"Dear {lead.customer_name or 'Sir/Madam'},\n\n"
            f"Please find attached our quotation {quotation.quotation_number} "
            f"for your recent enquiry.\n\n"
            f"Should you have any questions or require further clarification, "
            f"please do not hesitate to reach out.\n\n"
            f"Regards,\nFerrite Steel"
        )
        to_email = lead.customer_email
    return render(request, 'quotations/quotation_send_confirm.html', {
        'quotation': quotation,
        'to_email': to_email,
        'subject': default_subject,
        'body': default_body,
    })


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

        # Customer lookup before LLM call so entity_notes and transport are available
        customer = _find_customer(lead) if not lead.broker else None
        if lead.broker:
            entity_notes = lead.broker.notes
        else:
            entity_notes = customer.notes if customer else ''

        # Attempt LLM pre-fill; fall back silently on any failure
        try:
            draft = generate_quotation_draft(lead, entity_notes)
            quotation.llm_raw_response = str(draft)

            for field in ('payment_terms', 'delivery_address', 'transport_extra',
                          'sgst_percent', 'cgst_percent', 'notes', 'valid_until'):
                if draft.get(field) not in (None, ''):
                    setattr(quotation, field, draft[field])
            quotation.save()

            for item in draft.get('line_items', []):
                qty = Decimal(str(item.get('quantity') or 0))
                price = Decimal(str(item.get('unit_price') or 0))
                uom = item.get('uom', 'ton')
                tons = qty / Decimal('1000') if uom == 'kg' else qty
                QuotationLineItem.objects.create(
                    quotation=quotation,
                    hsn_code=item.get('hsn_code', ''),
                    product_name=item.get('product_name', ''),
                    length=item.get('length'),
                    pcs=item.get('pcs'),
                    quantity=qty,
                    uom=uom,
                    unit_price=price,
                    total_price=tons * price,
                    notes=item.get('notes', ''),
                )
        except Exception:
            pass

        # Pre-fill transport and delivery address from returning customer
        if not lead.broker:
            address = (customer.billing_address if customer else '') or lead.location
            update_fields = []
            if customer and quotation.transport_extra == Decimal('0') and customer.transport_extra:
                quotation.transport_extra = customer.transport_extra
                update_fields.append('transport_extra')
            if not quotation.delivery_address and address:
                quotation.delivery_address = address
                update_fields.append('delivery_address')
            if update_fields:
                quotation.save(update_fields=update_fields)
            if not customer:
                _upsert_customer(lead, Decimal('0'))

        messages.success(request, f'{quotation} created as draft.')
        return redirect('quotation_edit', pk=quotation.pk)
    return redirect('quotation_select_lead')


@login_required
def quotation_delete(request, pk):
    if request.method != 'POST':
        return redirect('quotation_detail', pk=pk)
    quotation = get_object_or_404(Quotation, pk=pk)
    number = quotation.quotation_number
    quotation.delete()
    messages.success(request, f'{number} deleted.')
    return redirect('quotation_list')


@login_required
def lead_delete(request, pk):
    if request.method != 'POST':
        return redirect('lead_detail', pk=pk)
    lead = get_object_or_404(Lead, pk=pk)
    name = lead.customer_name or f'Lead #{lead.pk}'
    lead.delete()
    messages.success(request, f'Lead "{name}" and all its quotations deleted.')
    return redirect('lead_list')


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

@login_required
def market_order_do_send(request, pk):
    if not _require_market_or_admin(request):
        return redirect('dashboard')
    order = get_object_or_404(MarketOrder, pk=pk)

    if request.method == 'POST':
        do_number = request.POST.get('do_number', '').strip()
        if do_number:
            order.do_number = do_number
            order.do_issued_at = timezone.now()
            order.status = 'completed'
            order.save(update_fields=['do_number', 'do_issued_at', 'status'])

        if request.POST.get('confirm_send') and order.broker.email:
            from django.core.mail import send_mail
            send_mail(
                subject=f'Delivery Order — {order.broker.name}',
                message=(
                    f'Dear {order.broker.name},\n\n'
                    f'Your Delivery Order number is: {order.do_number}\n\n'
                    f'Regards,\nFerrite Steel'
                ),
                from_email=None,
                recipient_list=[order.broker.email],
                fail_silently=False,
            )
            messages.success(request, f'DO number sent to {order.broker.email}.')
            return redirect('market_order_detail', pk=order.pk)

        return render(request, 'quotations/market_order_do_send.html', {'order': order})

    return render(request, 'quotations/market_order_do_send.html', {'order': order})

@login_required
@require_POST
def poll_emails_now(request):
    try:
        call_command('poll_emails')
        messages.success(request, 'Inbox polled successfully')
    except Exception as exc:
        messages.error(request, f"Poll failed: {exc}")
    return redirect(request.META.get('HTTP_REFERER', '/'))