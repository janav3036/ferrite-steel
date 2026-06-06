from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.
class CustomUser(AbstractUser):
    TEAM_CHOICES = [
        ('team_9',    'Team 9'),
        ('cs',        'CS Team'),
        ('market',    'Market Team'),
        ('corporate', 'Corporate Team'),
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
    employee_id = models.IntegerField(blank=True, null=True)
    branch = models.CharField(max_length=20,blank=True, null=True)

    class Meta:
        permissions = [
            ('can_manage_users', 'Can manage users'),
            ('can_view_user_list', 'Can view user list'),
        ]