from decimal import Decimal

from django.conf import settings
from django.db import models


class Product(models.Model):
    MAKE_CHOICES = [
        ('main', 'Main'),
        ('rolling', 'Rolling'),
        ('plate', 'Plate'),
    ]
    SUB_TYPE_CHOICES = [
        ('angle', 'Angle'),
        ('channel', 'Channel'),
        ('ub', 'UB'),
        ('uc', 'UC'),
        ('beam', 'Beam'),
        ('flat', 'Flat'),
        ('red_material', 'Red Material'),
        ('tmt', 'TMT'),
    ]
    # Valid sub-types per type (used for form-side JS validation)
    SUB_TYPE_MAP = {
        'main': ['angle', 'channel', 'ub', 'uc', 'beam', 'red_material', 'tmt'],
        'rolling': ['angle', 'channel', 'beam', 'flat'],
        'plate': [],
    }

    hsn_code = models.CharField(max_length=20, blank=True)
    make = models.CharField(max_length=10, choices=MAKE_CHOICES)
    sub_type = models.CharField(max_length=20, choices=SUB_TYPE_CHOICES, blank=True)
    size = models.CharField(max_length=100)
    length = models.CharField(max_length=50, blank=True)
    pieces = models.IntegerField(null=True, blank=True)
    SITE_CHOICES = [
        ('site_1', 'Site 1'),
        ('site_2', 'Site 2'),
    ]

    grade = models.CharField(max_length=50, blank=True)
    godown = models.CharField(max_length=100, blank=True)
    site = models.CharField(max_length=10, choices=SITE_CHOICES, blank=True)
    quantity = models.DecimalField(max_digits=12, decimal_places=3)
    rate = models.DecimalField(max_digits=12, decimal_places=2)
    is_active = models.BooleanField(default=True)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Product'
        verbose_name_plural = 'Products'
        ordering = ['make', 'sub_type', 'size']

    def __str__(self):
        parts = [self.hsn_code, self.get_sub_type_display() or self.get_make_display(), self.size]
        if self.length:
            parts.append(self.length)
        return ' — '.join(parts)


class Customer(models.Model):
    TEAM_CHOICES = [
        ('team_9', 'Team 9'),
        ('cs', 'CS Team'),
        ('market', 'Market Team'),
        ('corporate', 'Corporate Team'),
    ]
    PAYMENT_TERMS_CHOICES = [
        ('advance', 'Advance'),
        ('cash', 'Cash'),
    ]

    customer_code = models.CharField(max_length=30, unique=True, null=True, blank=True)
    name = models.CharField(max_length=255)
    company = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    gst_number = models.CharField(max_length=20, blank=True)
    billing_address = models.TextField(blank=True)
    shipping_address = models.TextField(blank=True)
    payment_terms = models.CharField(max_length=10, choices=PAYMENT_TERMS_CHOICES, blank=True)
    transport_extra = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    loading_rate = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.5'))
    notes = models.TextField(blank=True, help_text='AI context: discount preferences, special terms, etc.')
    competitors = models.TextField(blank=True, help_text='One competitor per line.')
    rm = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='managed_customers',
        verbose_name='Relationship Manager',
    )
    handling_team = models.CharField(max_length=20, choices=TEAM_CHOICES, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Customer'
        verbose_name_plural = 'Customers'
        ordering = ['name']

    def __str__(self):
        return f'{self.name} ({self.company})' if self.company else self.name


class Broker(models.Model):
    name = models.CharField(max_length=255)
    company = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    location = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True, help_text='AI context: usual margins, preferred products, etc.')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Broker'
        verbose_name_plural = 'Brokers'
        ordering = ['name']

    def __str__(self):
        return f'{self.name} ({self.company})' if self.company else self.name
