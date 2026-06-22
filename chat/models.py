from django.db import models
from django.conf import settings


class ChatMessage(models.Model):
    CHANNEL_CHOICES = [
        ('all_staff', 'All Staff'),
        ('team_9',           'Team 9'),
        ('cs',               'CS Team'),
        ('market',           'Market Team'),
        ('corporate',        'Corporate Team'),
        ('marketing',        'Marketing'),
        ('accounts',         'Accounts'),
        ('billing_dispatch', 'Billing Dispatch'),
        ('tender',           'Tender'),
        ('quality',          'Quality'),
        ('collection',       'Collection'),
    ]

    LINK_TYPE_CHOICES = [
        ('quotation',    'Quotation'),
        ('lead',         'Lead'),
        ('customer',     'Customer'),
    ]

    channel         = models.CharField(max_length=30, choices=CHANNEL_CHOICES, default='all_staff')
    sender          = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='chat_messages')
    content         = models.TextField(blank=True)
    attachment      = models.FileField(upload_to='chat_attachments/', blank=True)
    attachment_name = models.CharField(max_length=255, blank=True)
    link_type       = models.CharField(max_length=30, choices=LINK_TYPE_CHOICES, blank=True)
    link_id         = models.IntegerField(null=True, blank=True)
    link_label      = models.CharField(max_length=255, blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Chat Message'
        verbose_name_plural = 'Chat Messages'
        ordering = ['created_at']

    def __str__(self):
        return f"{self.sender.username} in #{self.channel}: {self.content[:60]}"
