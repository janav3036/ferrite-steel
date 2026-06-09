from django.db import models
from django.conf import settings


class ChatMessage(models.Model):
    CHANNEL_CHOICES = [
        ('all_staff', 'All Staff'),
        ('team_9',    'Team 9'),
        ('cs',        'CS Team'),
        ('market',    'Market Team'),
        ('corporate', 'Corporate Team'),
    ]

    channel    = models.CharField(max_length=30, choices=CHANNEL_CHOICES, default='all_staff')
    sender     = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='chat_messages')
    content    = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Chat Message'
        verbose_name_plural = 'Chat Messages'
        ordering = ['created_at']

    def __str__(self):
        return f"{self.sender.username} in #{self.channel}: {self.content[:60]}"
