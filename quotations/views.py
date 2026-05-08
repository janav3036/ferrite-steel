from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from .forms import ManualLeadForm
from .models import Lead, Quotation


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
    unquoted_leads = Lead.objects.filter(quotations__isnull = True)
    return render(request, 'quotations/quotation_list.html', {'quotations': quotations, 'unquoted_leads': unquoted_leads})


@login_required
def quotation_detail(request, pk):
    quotation = get_object_or_404(
        Quotation.objects.select_related('lead', 'created_by', 'approved_by').prefetch_related('line_items'),
        pk=pk,
    )
    return render(request, 'quotations/quotation_detail.html', {'quotation': quotation})


@login_required
def quotation_approve(request, pk):
    if request.user.role not in ('manager', 'admin'):
        messages.error(request, 'Only managers and admins can approve quotations.')
        return redirect('quotation_detail', pk=pk)

    quotation = get_object_or_404(Quotation, pk=pk, status='draft')
    if request.method == 'POST':
        quotation.status = 'approved'
        quotation.approved_by = request.user
        quotation.approved_at = timezone.now()
        quotation.save()
        messages.success(request, f'{quotation} approved.')
    return redirect('quotation_detail', pk=pk)
