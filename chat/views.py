from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_POST
from .models import ChatMessage

CHANNEL_LABELS = {
    'all_staff': 'All Staff',
    'team_9':    'Team 9',
    'cs':        'CS Team',
    'market':    'Market Team',
    'corporate': 'Corporate Team',
}


def _accessible_channels(user):
    channels = ['all_staff']
    if user.team and user.team in CHANNEL_LABELS:
        channels.append(user.team)
    if user.role == 'admin' or user.is_superuser:
        channels = list(CHANNEL_LABELS.keys())
    return channels


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

    channel_data = [
        {'slug': c, 'label': CHANNEL_LABELS[c]}
        for c in channels
    ]

    return render(request, 'chat/chat.html', {
        'channels': channel_data,
        'active_channel': active,
        'active_label': CHANNEL_LABELS.get(active, active),
        'messages': messages_qs,
    })


@login_required
@require_POST
def chat_send(request):
    channel = request.POST.get('channel', 'all_staff')
    content = request.POST.get('content', '').strip()
    if not content:
        return JsonResponse({'ok': False, 'error': 'Empty message'}, status=400)

    accessible = _accessible_channels(request.user)
    if channel not in accessible:
        return JsonResponse({'ok': False, 'error': 'Access denied'}, status=403)

    msg = ChatMessage.objects.create(channel=channel, sender=request.user, content=content)
    return JsonResponse({
        'ok': True,
        'id': msg.pk,
        'sender': msg.sender.get_full_name() or msg.sender.username,
        'initials': msg.sender.username[:2].upper(),
        'content': msg.content,
        'time': msg.created_at.strftime('%H:%M'),
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
    data = [{
        'id': m.pk,
        'sender': m.sender.get_full_name() or m.sender.username,
        'initials': m.sender.username[:2].upper(),
        'content': m.content,
        'time': m.created_at.strftime('%H:%M'),
        'is_me': m.sender_id == request.user.pk,
    } for m in qs]
    return JsonResponse({'messages': data})
