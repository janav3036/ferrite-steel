from decimal import Decimal

from django.db import models
from django.conf import settings


class PricingEntry(models.Model):
    product_name = models.CharField(max_length=255)
    product_code = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=100, blank=True)
    unit = models.CharField(max_length=50)
    base_price = models.DecimalField(max_digits=12, decimal_places=2)
    min_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    is_active = models.BooleanField(default=True)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Pricing Entry'
        verbose_name_plural = 'Pricing Entries'
        ordering = ['category', 'product_name']

    def __str__(self):
        return f'{self.product_code} — {self.product_name}'


class Customer(models.Model):
    name = models.CharField(max_length=255)
    company = models.CharField(max_length=255, blank=True)
    location = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    transport_extra = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    loading_rate = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.5'))
    notes = models.TextField(blank=True, help_text='AI context: discount preferences, special terms, etc.')
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


class Lead(models.Model):
    SOURCE_CHOICES = [
        ('whatsapp', 'WhatsApp'),
        ('email', 'Email'),
        ('manual', 'Manual Entry'),
    ]
    STATUS_CHOICES = [
        ('new', 'New'),
        ('processing', 'Processing'),
        ('quoted', 'Quoted'),
        ('rejected', 'Rejected'),
    ]

    source = models.CharField(max_length=20, choices=SOURCE_CHOICES)
    raw_text = models.TextField(help_text='Original message or enquiry text')
    customer_name = models.CharField(max_length=255, blank=True)
    customer_phone = models.CharField(max_length=30, blank=True)
    customer_email = models.EmailField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    industry = models.CharField(max_length=100, blank=True)
    company = models.CharField(max_length=100, blank=True)
    location = models.CharField(max_length=100, blank=True)
    broker = models.ForeignKey(
        'Broker',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='leads',
    )
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='leads_created',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Lead'
        verbose_name_plural = 'Leads'
        ordering = ['-created_at']

    def __str__(self):
        return f'Lead #{self.pk} — {self.customer_name or "Unknown"} ({self.get_source_display()})'


class Quotation(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('approved', 'Approved'),
        ('sent', 'Sent'),
    ]

    OUTCOME_CHOICES = [
        ('win', 'Win'),
        ('loss', 'Loss'),
        ('not_updated', 'Not Updated'),
    ]

    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='quotations')
    parent_quotation = models.ForeignKey(
        'self', null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='revisions',
    )
    version = models.IntegerField(default=1)
    quotation_number = models.CharField(max_length=50, unique=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    outcome = models.CharField(max_length=20, choices=OUTCOME_CHOICES, default='not_updated')
    llm_raw_response = models.TextField(blank=True)
    total_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    valid_until = models.DateField(null=True, blank=True)
    payment_terms = models.CharField(max_length=100, default='Advance')
    delivery_address = models.TextField(blank=True)
    transport_extra = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    sgst_percent = models.DecimalField(max_digits=5, decimal_places=2, default=9)
    cgst_percent = models.DecimalField(max_digits=5, decimal_places=2, default=9)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='quotations_created',
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='quotations_approved',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Quotation'
        verbose_name_plural = 'Quotations'
        ordering = ['-created_at']

    def __str__(self):
        return self.quotation_number or f'Quotation #{self.pk}'

    def save(self, *args, **kwargs):
        if not self.quotation_number:
            super().save(*args, **kwargs)
            if self.parent_quotation:
                root_num = self.parent_quotation.quotation_number.split('-v')[0]
                self.quotation_number = f'{root_num}-v{self.version}'
            else:
                self.quotation_number = f'QT-{self.pk:05d}'
            Quotation.objects.filter(pk=self.pk).update(quotation_number=self.quotation_number)
        else:
            super().save(*args, **kwargs)


class QuotationLineItem(models.Model):
    quotation = models.ForeignKey(Quotation, on_delete=models.CASCADE, related_name='line_items')
    product_name = models.CharField(max_length=255)
    make = models.CharField(max_length=100, blank=True)
    length = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    pcs = models.IntegerField(null=True, blank=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    total_price = models.DecimalField(max_digits=14, decimal_places=2)
    notes = models.CharField(max_length=500, blank=True)

    class Meta:
        verbose_name = 'Line Item'
        verbose_name_plural = 'Line Items'

    def __str__(self):
        return f'{self.product_name} * {self.quantity}'


class MarketOrder(models.Model):
    STATUS_CHOICES = [
        ('new',              'New Order'),
        ('rate_sent',        'Rate Sent to Broker'),
        ('broker_confirmed', 'Broker Confirmed'),
        ('do_pending',       'DO Pending'),
        ('completed',        'Completed'),
        ('cancelled',        'Cancelled'),
    ]
    SUB_TEAM_CHOICES = [
        ('primary', 'Primary'),
        ('rolling', 'Rolling'),
    ]

    broker = models.ForeignKey(
        Broker, on_delete=models.CASCADE, related_name='orders',
    )
    quotation = models.ForeignKey(
        Quotation, null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='market_orders',
    )
    sub_team = models.CharField(max_length=20, choices=SUB_TEAM_CHOICES)
    product_details = models.TextField(help_text='What the broker ordered')
    quantity = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='new')

    rate = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    rate_sent_at = models.DateTimeField(null=True, blank=True)

    broker_confirmed_at = models.DateTimeField(null=True, blank=True)

    loading_dock_member = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='loading_dock_orders',
    )
    do_requested_at = models.DateTimeField(null=True, blank=True)
    do_number = models.CharField(max_length=100, blank=True)
    do_issued_at = models.DateTimeField(null=True, blank=True)

    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True,
        on_delete=models.SET_NULL,
        related_name='market_orders_created',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Market Order'
        verbose_name_plural = 'Market Orders'
        ordering = ['-created_at']

    def __str__(self):
        return f'MO-{self.pk:05d} — {self.broker.name} ({self.get_status_display()})'
