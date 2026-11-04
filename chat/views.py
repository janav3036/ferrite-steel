from datetime import timedelta
from itertools import groupby

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST
from .models import ChatMessage, ChatReadState
from aegis.models import CustomUser


def _day_label(d):
    """WhatsApp-style date divider label — 'Today'/'Yesterday', else the date."""
    today = timezone.localdate()
    if d == today:
        return 'Today'
    if d == today - timedelta(days=1):
        return 'Yesterday'
    return d.strftime('%d %B %Y')

CHANNEL_LABELS = {
    'all_staff':        'All Staff',
    'team_9':           'Team 9',
    'cs':               'CS Team',
    'market':           'Market Team',
    'corporate':        'Corporate Team',
    'marketing':        'Marketing',
    'accounts':         'Accounts',
    'billing_dispatch': 'Billing Dispatch',
    'tender':           'Tender',
    'quality':          'Quality',
    'collection':       'Collection',
}

LINK_ICONS = {
    'quotation': '📋',
    'lead':      '📥',
    'customer':  '🏢',
}


def _accessible_channels(user):
    channels = ['all_staff']
    if user.team and user.team in CHANNEL_LABELS:
        channels.append(user.team)
    if user.role == 'admin' or user.is_superuser:
        channels = list(CHANNEL_LABELS.keys())
    return channels


def _channel_members(channel):
    if channel == 'all_staff':
        return CustomUser.objects.filter(is_active=True)
    return CustomUser.objects.filter(is_active=True).filter(
        Q(team=channel) | Q(role='admin') | Q(is_superuser=True)
    )


def _mark_read(user, channel, up_to_id):
    if not up_to_id:
        return
    state, created = ChatReadState.objects.get_or_create(
        user=user, channel=channel, defaults={'last_read_id': up_to_id}
    )
    if not created and up_to_id > state.last_read_id:
        state.last_read_id = up_to_id
        state.save(update_fields=['last_read_id', 'updated_at'])


def _link_url(link_type, link_id):
    try:
        if link_type == 'quotation':
            return reverse('quotation_detail', args=[link_id])
        if link_type == 'lead':
            return reverse('lead_detail', args=[link_id])
        if link_type == 'customer':
            return reverse('customer_detail', args=[link_id])
    except Exception:
        pass
    return '#'


def _msg_dict(m, current_user_id):
    local_created = timezone.localtime(m.created_at)
    d = {
        'id': m.pk,
        'sender': m.sender.get_full_name() or m.sender.username,
        'initials': m.sender.username[:2].upper(),
        'content': m.content,
        # strftime('%H:%M') on the raw (UTC) datetime would show the wrong
        # clock time — always format the localized (Asia/Kolkata) version.
        'time': local_created.strftime('%H:%M'),
        'date_label': _day_label(local_created.date()),
        'is_me': m.sender_id == current_user_id,
        'attachment_url': m.attachment.url if m.attachment else '',
        'attachment_name': m.attachment_name,
        'link_type': m.link_type,
        'link_label': m.link_label,
        'link_url': _link_url(m.link_type, m.link_id) if m.link_type else '',
        'link_icon': LINK_ICONS.get(m.link_type, '🔗'),
    }
    return d


@login_required
def chat_home(request):
    channels = _accessible_channels(request.user)
    active = request.GET.get('channel', 'all_staff')
    if active not in channels:
        active = channels[0]

    messages_qs = list(
        ChatMessage.objects.filter(channel=active).select_related('sender').order_by('-created_at')[:100]
    )
    messages_qs.reverse()
    if messages_qs:
        _mark_read(request.user, active, messages_qs[-1].pk)

    read_states = {
        rs.channel: rs.last_read_id
        for rs in ChatReadState.objects.filter(user=request.user, channel__in=channels)
    }
    channel_data = [
        {
            'slug': c,
            'label': CHANNEL_LABELS[c],
            'unread': ChatMessage.objects.filter(channel=c, pk__gt=read_states.get(c, 0)).count(),
        }
        for c in channels
    ]

    message_days = [
        {'label': _day_label(day), 'messages': list(msgs)}
        for day, msgs in groupby(messages_qs, key=lambda m: timezone.localtime(m.created_at).date())
    ]

    return render(request, 'chat/chat.html', {
        'channels': channel_data,
        'active_channel': active,
        'active_label': CHANNEL_LABELS.get(active, active),
        'message_days': message_days,
        'link_icons': LINK_ICONS,
    })


@login_required
@require_POST
def chat_send(request):
    channel = request.POST.get('channel', 'all_staff')
    content = request.POST.get('content', '').strip()
    link_type = request.POST.get('link_type', '').strip()
    link_id_raw = request.POST.get('link_id', '').strip()
    link_label = request.POST.get('link_label', '').strip()
    uploaded_file = request.FILES.get('attachment')

    if not content and not link_type and not uploaded_file:
        return JsonResponse({'ok': False, 'error': 'Empty message'}, status=400)

    accessible = _accessible_channels(request.user)
    if channel not in accessible:
        return JsonResponse({'ok': False, 'error': 'Access denied'}, status=403)

    link_id = int(link_id_raw) if link_id_raw.isdigit() else None

    msg = ChatMessage(channel=channel, sender=request.user, content=content)
    if uploaded_file:
        msg.attachment = uploaded_file
        msg.attachment_name = uploaded_file.name
    if link_type and link_id:
        msg.link_type = link_type
        msg.link_id = link_id
        msg.link_label = link_label
    msg.save()

    return JsonResponse({
        'ok': True,
        **_msg_dict(msg, request.user.pk),
        'is_me': True,
    })


@login_required
def chat_poll(request):
    channel = request.GET.get('channel', 'all_staff')
    since_id = int(request.GET.get('since', 0))

    accessible = _accessible_channels(request.user)
    if channel not in accessible:
        return JsonResponse({'messages': []})

    qs = ChatMessage.objects.filter(channel=channel, pk__gt=since_id).select_related('sender').order_by('created_at')
    data = [_msg_dict(m, request.user.pk) for m in qs]
    latest_id = data[-1]['id'] if data else since_id
    _mark_read(request.user, channel, latest_id)
    return JsonResponse({'messages': data})


@login_required
def chat_channels_json(request):
    channels = _accessible_channels(request.user)
    data = [{'slug': c, 'label': CHANNEL_LABELS[c]} for c in channels]
    return JsonResponse({'channels': data})


@login_required
def chat_search(request):
    from quotations.models import Lead, Quotation
    from database.models import Customer

    entity_type = request.GET.get('type', '')
    q = request.GET.get('q', '').strip()
    results = []

    if entity_type == 'quotation' and q:
        qs = Quotation.objects.select_related('lead').filter(
            quotation_number__icontains=q
        ) | Quotation.objects.select_related('lead').filter(
            lead__company__icontains=q
        )
        for obj in qs.distinct()[:8]:
            results.append({
                'id': obj.pk,
                'label': f"{obj.quotation_number} — {obj.lead.company if obj.lead else ''}",
            })

    elif entity_type == 'lead' and q:
        qs = Lead.objects.filter(company__icontains=q) | Lead.objects.filter(customer_name__icontains=q)
        for obj in qs.distinct()[:8]:
            results.append({
                'id': obj.pk,
                'label': f"{obj.company or obj.customer_name}",
            })

    elif entity_type == 'customer' and q:
        qs = Customer.objects.filter(name__icontains=q) | Customer.objects.filter(company__icontains=q)
        for obj in qs.distinct()[:8]:
            results.append({
                'id': obj.pk,
                'label': obj.name or obj.company,
            })

    return JsonResponse({'results': results})


@login_required
def chat_read_status(request):
    channel = request.GET.get('channel', 'all_staff')
    accessible = _accessible_channels(request.user)
    if channel not in accessible:
        return JsonResponse({'members': []})

    members = _channel_members(channel).exclude(pk=request.user.pk)
    states = {
        s.user_id: s.last_read_id
        for s in ChatReadState.objects.filter(channel=channel, user__in=members)
    }
    data = [
        {
            'user_id': m.pk,
            'name': m.get_full_name() or m.username,
            'last_read_id': states.get(m.pk, 0),
        }
        for m in members
    ]
    return JsonResponse({'members': data}) 