from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail

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
        ('closed', 'Closed'),
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
        'database.Broker',
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

    PAYMENT_TERMS_CHOICES = [
        ('Advance', 'Advance'),
        ('Cash', 'Cash'),
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
    winning_quotation = models.ForeignKey(
        'self', null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='won_as',
    )
    stock_deducted = models.BooleanField(default=False)
    llm_raw_response = models.TextField(blank=True)
    total_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    valid_until = models.DateField(null=True, blank=True)
    payment_terms = models.CharField(max_length=100, choices=PAYMENT_TERMS_CHOICES, default='Advance')
    delivery_address = models.TextField(blank=True)
    loading_extra = models.DecimalField(max_digits=12, decimal_places=2, default=0)
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
    UOM_CHOICES = [
        ('ton', 'T'),
        ('kg', 'KG'),
    ]

    quotation = models.ForeignKey(Quotation, on_delete=models.CASCADE, related_name='line_items')
    product = models.ForeignKey(
        'database.Product', null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='line_items',
    )
    hsn_code = models.CharField(max_length=20, blank=True)
    product_name = models.CharField(max_length=255)
    make = models.CharField(max_length=100, blank=True)
    length = models.CharField(max_length=50, blank=True)
    pcs = models.IntegerField(null=True, blank=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=3)
    uom = models.CharField(max_length=3, choices=UOM_CHOICES, default='ton')
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    total_price = models.DecimalField(max_digits=14, decimal_places=2)
    discount_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Line Item'
        verbose_name_plural = 'Line Items'

    def __str__(self):
        return f'{self.product_name} * {self.quantity}'

    @property
    def final_price(self):
        from decimal import Decimal
        if self.discount_pct:
            return self.total_price * (1 - self.discount_pct / Decimal('100'))
        return self.total_price


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
        'database.Broker', on_delete=models.CASCADE, related_name='orders',
    )
    quotation = models.ForeignKey(
        Quotation, null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='market_orders',
    )
    lead = models.ForeignKey(
        Lead, 
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='market_orders'
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


class ProductKeyword(models.Model):
    keyword   = models.CharField(max_length=100, help_text='What clients say, e.g. "sariya", "patti", "12mm rod"')
    maps_to   = models.CharField(max_length=100, help_text='Canonical product name, e.g. "TMT Bars 12mm"')
    notes     = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Product Keyword'
        verbose_name_plural = 'Product Keywords'
        ordering = ['keyword']

    def __str__(self):
        return f'{self.keyword} → {self.maps_to}'


class TeamEmailConfig(models.Model):
    TEAM_CHOICES = [
        ('team_9',    'Team 9'),
        ('cs',        'CS Team'),
        ('market',    'Market Team'),
        ('corporate', 'Corporate Team'),
    ]

    team          = models.CharField(max_length=20, choices=TEAM_CHOICES, unique=True)
    email_address = models.EmailField(help_text='Shared team inbox, e.g. enquiry@ferrite.in')
    imap_host     = models.CharField(max_length=255, default='imap.gmail.com')
    imap_port     = models.IntegerField(default=993)
    imap_username = models.EmailField()
    imap_password = models.CharField(max_length=255, help_text='Use an App Password, not the account password')
    use_ssl       = models.BooleanField(default=True)
    is_active     = models.BooleanField(default=True)
    poll_interval_minutes = models.IntegerField(
        default=30, 
        help_text = 'How often to poll this inbox automatically (minutes)'

    )
    last_polled_at = models.DateTimeField(
        null=True, blank=True,
        help_text="set automatically after each successful poll"
    )

    class Meta:
        verbose_name = 'Team Email Config'
        verbose_name_plural = 'Team Email Configs'
        ordering = ['team']

    def __str__(self):
        return f'{self.get_team_display()} — {self.email_address}'


@receiver(post_save, sender=MarketOrder)
def notify_loading_dock(sender, instance, **kwargs):
    update_fields = kwargs.get('update_fields') or []
    if instance.status != 'broker_confirmed' or 'status' not in update_fields:
        return
    if not instance.loading_dock_member or not instance.loading_dock_member.email:
        return
    send_mail(
        subject=f'New Order Confirmed — MO-{instance.pk:05d}',
        message=(
            f'Broker {instance.broker.name} has confirmed the order.\n\n'
            f'Order: MO-{instance.pk:05d}\n'
            f'Product: {instance.product_details}\n'
            f'Quantity: {instance.quantity}\n\n'
            f'Please issue the Delivery Order.'
        ),
        from_email=None,
        recipient_list=[instance.loading_dock_member.email],
        fail_silently=True,
    )