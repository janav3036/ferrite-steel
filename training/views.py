from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Case
from .forms import CaseForm


@login_required
def training_home(request):
    if not request.user.has_perm('training.view_case'):
        messages.error(request, 'You do not have access to Training.')
        return redirect('dashboard')
    user = request.user
    if user.is_superuser or user.role == 'admin':
        case_count = Case.objects.count()
    else:
        case_count = Case.objects.filter(departments__contains=user.team).count()
    return render(request, 'training/home.html', {'case_count': case_count})


@login_required
def case_list(request):
    if not request.user.has_perm('training.view_case'):
        messages.error(request, 'You do not have permission to view cases.')
        return redirect('dashboard')
    user = request.user
    if user.is_superuser or user.role == 'admin':
        cases = Case.objects.select_related('customer', 'created_by').all()
    else:
        cases = Case.objects.select_related('customer', 'created_by').filter(
            departments__contains=user.team
        )
    return render(request, 'training/case_list.html', {'cases': cases})


@login_required
def case_detail(request, pk):
    if not request.user.has_perm('training.view_case'):
        messages.error(request, 'You do not have access to cases.')
        return redirect('dashboard')
    case = get_object_or_404(Case, pk=pk)
    user = request.user
    if not user.is_superuser and user.role != 'admin':
        if user.team not in (case.departments or []):
            messages.error(request, 'You do not have access to this case.')
            return redirect('case_list')
    return render(request, 'training/case_detail.html', {'case': case})


@login_required
def case_create(request):
    if not request.user.has_perm('training.add_case'):
        messages.error(request, 'You do not have permission to create cases.')
        return redirect('case_list')
    initial = {}
    notes = request.GET.get('notes', '')
    lead_pk = request.GET.get('lead', '')
    if notes:
        initial['problem_description'] = notes
    if request.method == 'POST':
        form = CaseForm(request.POST)
        if form.is_valid():
            case = form.save(commit=False)
            case.created_by = request.user
            case.departments = form.cleaned_data['departments']
            case.save()
            messages.success(request, 'Case created.')
            return redirect('case_detail', pk=case.pk)
    else:
        form = CaseForm(initial=initial)
    return render(request, 'training/case_create.html', {
        'form': form,
        'lead_pk': lead_pk,
    })


@login_required
def case_edit(request, pk):
    if not request.user.has_perm('training.change_case'):
        messages.error(request, 'You do not have permission to edit cases.')
        return redirect('case_list')
    case = get_object_or_404(Case, pk=pk)
    if request.method == 'POST':
        form = CaseForm(request.POST, instance=case)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.departments = form.cleaned_data['departments']
            obj.save()
            messages.success(request, 'Case updated.')
            return redirect('case_detail', pk=case.pk)
    else:
        form = CaseForm(instance=case, initial={'departments': case.departments})
    return render(request, 'training/case_edit.html', {'form': form, 'case': case})


@login_required
def case_delete(request, pk):
    if not request.user.has_perm('training.delete_case'):
        messages.error(request, 'You do not have permission to delete cases.')
        return redirect('case_list')
    case = get_object_or_404(Case, pk=pk)
    if request.method == 'POST':
        case.delete()
        messages.success(request, 'Case deleted.')
        return redirect('case_list')
    return render(request, 'training/case_confirm_delete.html', {'case': case})
