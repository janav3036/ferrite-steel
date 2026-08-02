from decimal import Decimal

from django.conf import settings
from django.db import models


class Product(models.Model):
    CATEGORY_CHOICES = [
        ('main', 'Main'),
        ('rolling', 'Rolling'),
        ('jindal', 'Jindal'),
        ('others', 'Others'),
    ]
    UNIT_CHOICES = [
        ('ton', 'Ton'),
        ('kg', 'Kg'),
        ('mtr', 'Mtr'),
        ('nos', 'Nos'),
    ]

    item_no = models.CharField(max_length=20, blank=True)
    product_name = models.CharField(max_length=255)
    hsn_code = models.CharField(max_length=20, blank=True)
    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES, blank=True)
    unit = models.CharField(max_length=3, choices=UNIT_CHOICES, default='ton')
    quantity = models.DecimalField(max_digits=12, decimal_places=3)
    rate = models.DecimalField(max_digits=12, decimal_places=2)
    base_product = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='derived_products',
        verbose_name='Base Product',
        help_text='If set, effective rate = base product rate + offset below.',
    )
    rate_offset = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text='Added to the base product rate to get this product\'s effective rate (₹/T). Ignored if no base product is set.',
    )
    is_active = models.BooleanField(default=True)
    last_updated = models.DateTimeField(auto_now=True)

    @property
    def effective_rate(self):
        if self.base_product_id and self.base_product:
            return self.base_product.rate + self.rate_offset
        return self.rate

    class Meta:
        verbose_name = 'Product'
        verbose_name_plural = 'Products'
        ordering = ['category', 'item_no']

    def __str__(self):
        parts = [p for p in [self.item_no, self.product_name, self.hsn_code] if p]
        return ' — '.join(parts)


class Customer(models.Model):
    TEAM_CHOICES = [
        ('team_9',    'Team 9'),
        ('cs',        'CS Team'),
        ('market',    'Market Team'),
        ('corporate', 'Corporate Team'),
    ]
    PAYMENT_TERMS_CHOICES = [
        ('advance', 'Advance'),
        ('cash', 'Cash'),
    ]
    TYPE_OF_BUSINESS_CHOICES = [
        ('C', 'Commercial'),
        ('I', 'Industrial'),
        ('G', 'Government'),
    ]

    customer_code = models.CharField(max_length=30, unique=True, null=True, blank=True)
    name = models.CharField(max_length=255)
    company = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    gst_number = models.CharField(max_length=20, blank=True)
    pan_number = models.CharField(max_length=20, blank=True, verbose_name='PAN Number')
    msme_number = models.CharField(max_length=50, blank=True, verbose_name='MSME/Udhyan Number')
    city = models.CharField(max_length=100, blank=True)
    pincode = models.CharField(max_length=10, blank=True)
    billing_address = models.TextField(blank=True)
    shipping_address = models.TextField(blank=True)
    payment_terms = models.CharField(max_length=10, choices=PAYMENT_TERMS_CHOICES, blank=True)
    type_of_business = models.CharField(max_length=1, choices=TYPE_OF_BUSINESS_CHOICES, blank=True)
    transport_extra = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    loading_rate = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.5'))
    is_active = models.BooleanField(default=True)
    sap_created_at = models.DateField(null=True, blank=True, verbose_name='SAP Creation Date')
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
    credit_status = models.CharField(max_length=10, blank=True, choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ])
    last_assessed_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Customer'
        verbose_name_plural = 'Customers'
        ordering = ['name']
        permissions = [
            ('can_reassign_customer', 'Can reassign customer'),
        ]

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
