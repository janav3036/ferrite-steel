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
        ('rejected', 'Rejected'),
    ]

    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='quotations')
    quotation_number = models.CharField(max_length=50, unique=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    llm_raw_response = models.TextField(blank=True)
    total_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    valid_until = models.DateField(null=True, blank=True)
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
            self.quotation_number = f'QT-{self.pk:05d}'
            Quotation.objects.filter(pk=self.pk).update(quotation_number=self.quotation_number)
        else:
            super().save(*args, **kwargs)


class QuotationLineItem(models.Model):
    quotation = models.ForeignKey(Quotation, on_delete=models.CASCADE, related_name='line_items')
    product_name = models.CharField(max_length=255)
    product_code = models.CharField(max_length=100, blank=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=50)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    total_price = models.DecimalField(max_digits=14, decimal_places=2)
    notes = models.CharField(max_length=500, blank=True)

    class Meta:
        verbose_name = 'Line Item'
        verbose_name_plural = 'Line Items'

    def __str__(self):
        return f'{self.product_name} × {self.quantity} {self.unit}'
