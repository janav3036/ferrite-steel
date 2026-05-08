from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import get_object_or_404
from quotations.models import Lead, Quotation
from datetime import timedelta
from django.utils import timezone
from .forms import AddUserForm, EditRoleForm, RegistrationForm
from .models import CustomUser


@login_required
def dashboard(request):
    today = timezone.now()
    week_start = today - timedelta(days=today.weekday())

    if request.user.role in ('admin', 'manager'):
        leads = Lead.objects.filter(created_at__gte=week_start)
        quotations = Quotation.objects.filter(created_at__gte=week_start)
    else:
        leads = Lead.objects.filter(created_at__gte=week_start, created_by=request.user)
        quotations = Quotation.objects.filter(created_at__gte=week_start, created_by=request.user)
        
    context = {
        'total_leads': leads.count(),
        'leads_new': leads.filter(status='new').count(),
        'leads_processing': leads.filter(status='processing').count(),
        'leads_quoted': leads.filter(status='quoted').count(),
        'total_quotations': quotations.count(),
        'quotations_draft': quotations.filter(status='draft').count(),
        'quotations_approved': quotations.filter(status='approved').count(),
        'quotations_sent': quotations.filter(status='sent').count(),
    }

    return render(request, 'dashboard.html', context)


@login_required
def add_user(request):
    if request.user.role != 'admin':
        return redirect('dashboard')

    if request.method == 'POST':
        form = AddUserForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f"User '{form.cleaned_data['username']}' created successfully.")
            return redirect('add_user')
    else:
        form = AddUserForm()

    return render(request, 'add_user.html', {'form': form})

@login_required
def user_directory(request):
    if request.user.role != 'admin':
        return redirect('dashboard')

    users = CustomUser.objects.all().order_by('username')
    return render(request, 'directory.html', {'users':users})


@login_required
def edit_user_role(request, user_id):
    if request.user.role != 'admin':
        return redirect('dashboard')

    target_user = get_object_or_404(CustomUser, id=user_id)

    if request.method == 'POST':
        form = EditRoleForm(request.POST, instance=target_user)
        if form.is_valid():
            form.save()
            messages.success(request, f"{target_user.username}'s role updated.")
            return redirect('user_directory')
    else:
        form = EditRoleForm(instance=target_user)

    return render(request, 'edit_user_role.html', {'form': form, 'target_user': target_user})


def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            messages.success(request, 'Account request submitted. Wait for admin approval before logging in.')
            return redirect('login')
    else:
        form = RegistrationForm()

    return render(request, 'register.html', {'form': form})
    
@login_required
def approve_user(request, user_id):
    if request.user.role != 'admin':
        return redirect('dashboard')

    target_user = get_object_or_404(CustomUser, id=user_id)
    target_user.is_active = True
    target_user.save()
    messages.success(request, f"{target_user.username} has been approved.")
    return redirect('user_directory')


@login_required
def delete_user(request, user_id):
    if request.user.role != 'admin':
        return redirect('dashboard')

    if request.user.id == user_id:
        messages.error(request, "You cannot delete your own account.")
        return redirect('user_directory')

    target_user = get_object_or_404(CustomUser, id=user_id)
    username = target_user.username
    target_user.delete()
    messages.success(request, f"User '{username}' has been deleted.")
    return redirect('user_directory')
