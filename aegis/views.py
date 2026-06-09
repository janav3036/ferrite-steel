from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.views import PasswordResetView
from django.core.mail import get_connection, EmailMultiAlternatives
from django.http import JsonResponse
from django.template import loader
from django.contrib import messages
from quotations.models import Lead, Quotation
from datetime import timedelta
from django.utils import timezone
from .forms import AddUserForm, EditRoleForm, RegistrationForm, ProfileForm
from .models import CustomUser, Notification


@login_required
def dashboard(request):
    today = timezone.now()
    week_start = today - timedelta(days=today.weekday())

    if request.user.role in ('admin', 'lead'):
        leads = Lead.objects.filter(created_at__gte=week_start)
        quotations = Quotation.objects.filter(created_at__gte=week_start)
    else:
        leads = Lead.objects.filter(created_at__gte=week_start, created_by=request.user)
        quotations = Quotation.objects.filter(created_at__gte=week_start, created_by=request.user)
        
    recent_notifs = request.user.notifications.all()[:12]

    context = {
        'total_leads': leads.count(),
        'leads_new': leads.filter(status='new').count(),
        'leads_processing': leads.filter(status='processing').count(),
        'leads_quoted': leads.filter(status='quoted').count(),
        'total_quotations': quotations.count(),
        'quotations_draft': quotations.filter(status='draft').count(),
        'quotations_approved': quotations.filter(status='approved').count(),
        'quotations_sent': quotations.filter(status='sent').count(),
        'recent_notifs': recent_notifs,
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


@login_required
def profile(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated.')
            return redirect('profile')
    else:
        form = ProfileForm(instance=request.user)
    return render(request, 'profile.html', {'form': form})


class TeamPasswordResetForm(PasswordResetForm):
    def send_mail(self, subject_template_name, email_template_name, context,
                  from_email, to_email, html_email_template_name=None):
        from quotations.models import TeamEmailConfig
        config = TeamEmailConfig.objects.filter(is_active=True).first()
        connection = None
        if config:
            smtp_host = config.imap_host.replace('imap.', 'smtp.')
            connection = get_connection(
                backend='django.core.mail.backends.smtp.EmailBackend',
                host=smtp_host,
                port=587,
                username=config.imap_username,
                password=config.imap_password,
                use_tls=True,
            )
            from_email = config.email_address

        subject = loader.render_to_string(subject_template_name, context)
        subject = ''.join(subject.splitlines())
        body = loader.render_to_string(email_template_name, context)
        email = EmailMultiAlternatives(subject, body, from_email, [to_email], connection=connection)
        if html_email_template_name:
            html = loader.render_to_string(html_email_template_name, context)
            email.attach_alternative(html, 'text/html')
        email.send()


class CustomPasswordResetView(PasswordResetView):
    form_class = TeamPasswordResetForm
    template_name = 'registration/password_reset_form.html'
    email_template_name = 'registration/password_reset_email.html'
    subject_template_name = 'registration/password_reset_subject.txt'
    success_url = '/password-reset/done/'


# ── Notification views ────────────────────────────────────────────────────────

@login_required
def notifications_list(request):
    notifs = request.user.notifications.all()[:60]
    return render(request, 'notifications.html', {'notifs': notifs})


@login_required
def notification_mark_read(request, pk):
    notif = get_object_or_404(Notification, pk=pk, user=request.user)
    notif.is_read = True
    notif.save(update_fields=['is_read'])
    if notif.link:
        return redirect(notif.link)
    return redirect('notifications_list')


@login_required
def notifications_mark_all_read(request):
    if request.method == 'POST':
        request.user.notifications.filter(is_read=False).update(is_read=True)
    next_url = request.POST.get('next') or request.GET.get('next') or 'notifications_list'
    if next_url.startswith('/'):
        return redirect(next_url)
    return redirect('notifications_list')


@login_required
def notifications_unread_count(request):
    count = request.user.notifications.filter(is_read=False).count()
    return JsonResponse({'count': count})
