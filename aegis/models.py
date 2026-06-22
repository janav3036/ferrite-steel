from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser

# Create your models here.
class CustomUser(AbstractUser):
    TEAM_CHOICES = [
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

    ROLE_CHOICES = [
        ('admin',        'Admin'),
        ('lead',         'Team Lead'),
        ('member',       'Member'),
        ('primary',      'Primary Member'),
        ('rolling',      'Rolling Member'),
        ('loading_dock', 'Loading Dock'),
    ]

    team = models.CharField(max_length=20, choices=TEAM_CHOICES, blank=True, null=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    phone = models.CharField(max_length=20, blank=True, null=True)
    phone_2 = models.CharField(max_length=20, blank=True, null=True)
    employee_id = models.IntegerField(blank=True, null=True)
    branch = models.CharField(max_length=20,blank=True, null=True)

    class Meta:
        permissions = [
            ('can_manage_users', 'Can manage users'),
            ('can_view_user_list', 'Can view user list'),
        ]


class Notification(models.Model):
    NOTIF_TYPES = [
        ('lead_created',      'New Lead'),
        ('quotation_approved','Quotation Approved'),
        ('quotation_win',     'Quotation Won'),
        ('quotation_loss',    'Quotation Lost'),
        ('case_created',      'New Case'),
        ('market_confirmed',  'Order Confirmed'),
        ('market_do_pending', 'DO Requested'),
        ('market_completed',  'Order Completed'),
        ('general',           'General'),
    ]

    user       = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    title      = models.CharField(max_length=255)
    message    = models.TextField(blank=True)
    link       = models.CharField(max_length=500, blank=True)
    type       = models.CharField(max_length=30, choices=NOTIF_TYPES, default='general')
    is_read    = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user} — {self.title}"