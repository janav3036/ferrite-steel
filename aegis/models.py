from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.
class CustomUser(AbstractUser): 
    ROLE_CHOICES = [
        ('sales', 'Sales'),
        ('manager', 'Manager'),
        ('admin', 'Admin'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='sales')
    phone = models.CharField(max_length=20, blank=True, null=True)
    employee_id = models.IntegerField(blank=True, null=True)
    branch = models.CharField(max_length=20,blank=True, null=True)