from decimal import Decimal

from django.conf import settings
from django.db import models


class Product(models.Model):
    CATEGORY_CHOICES = [
        ('main', 'Main'),
        ('rolling', 'Rolling'),
        ('plate', 'Plate'),
    ]
    MAKE_CHOICES = [
        ('Jindal', 'Jindal'),
        ('Sail', 'Sail'),
        ('JSPL', 'JSPL'),
        ('TATA', 'TATA'),
        ('Posco', 'Posco'),
        ('RINL', 'RINL'),
        ('Rolling Apollo', 'Rolling Apollo'),
        ('Khanna', 'Khanna'),
        ('Essar / AMNS', 'Essar / AMNS'),
        ('Essar', 'Essar'),
        ('Goel', 'Goel'),
        ('VSP / SAIL', 'VSP / SAIL'),
        ('Sail / Jindal', 'Sail / Jindal'),
        ('Others', 'Others'),
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
        ('pipe', 'Pipe'),
        ('billet', 'Billet'),
        ('rail', 'Rail'),
        ('wire', 'Wire'),
        ('scrap', 'Scrap'),
    ]
    LENGTH_CHOICES = [
        ('6MTR', '6MTR'),
        ('12MTR', '12MTR'),
        ('5-6MTR', '5-6MTR'),
        ('10-12MTR', '10-12MTR'),
        ('7-12 MTR', '7-12 MTR'),
        ('2.5MTR', '2.5MTR'),
        ('8 feet', '8 feet'),
        ('10 feet', '10 feet'),
        ('12 feet', '12 feet'),
        ('14 feet', '14 feet'),
        ('16 feet', '16 feet'),
        ('20 feet', '20 feet'),
        ('2500', '2500'),
        ('3000', '3000'),
        ('3150', '3150'),
        ('5000', '5000'),
        ('6000', '6000'),
        ('6300', '6300'),
        ('8000', '8000'),
        ('10000', '10000'),
        ('12000', '12000'),
        ('CUTSIZE', 'CUTSIZE'),
        ('Random', 'Random'),
        ('Other', 'Other'),
    ]
    GRADE_CHOICES = [
        ('E250', 'E250'),
        ('E250ER', 'E250ER'),
        ('E250BO', 'E250BO'),
        ('E350BR', 'E350BR'),
        ('E350C', 'E350C'),
        ('516-GR 60', '516-GR 60'),
        ('516-GR 70', '516-GR 70'),
        ('C45', 'C45'),
        ('513D', '513D'),
        ('DD', 'DD'),
        ('FE500', 'FE500'),
        ('FE500D', 'FE500D'),
        ('HCRM', 'HCRM'),
        ('CRS', 'CRS'),
        ('1018', '1018'),
        ('EN8', 'EN8'),
        ('EN9', 'EN9'),
        ('AZ 70', 'AZ 70'),
        ('AZ 150', 'AZ 150'),
        ('AZ 150 C+', 'AZ 150 C+'),
        ('PPGI', 'PPGI'),
        ('PPGL', 'PPGL'),
        ('SHS', 'SHS'),
        ('IS4923', 'IS4923'),
        ('IS1161', 'IS1161'),
        ('SS304', 'SS304'),
        ('SS316', 'SS316'),
    ]
    # Valid sub-types per category (used for form-side JS validation)
    SUB_TYPE_MAP = {
        'main': ['angle', 'channel', 'ub', 'uc', 'beam', 'red_material', 'tmt', 'pipe', 'billet', 'rail', 'wire', 'scrap'],
        'rolling': ['angle', 'channel', 'beam', 'flat'],
        'plate': [],
    }

    hsn_code = models.CharField(max_length=20, blank=True)
    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES)
    make = models.CharField(max_length=30, choices=MAKE_CHOICES, blank=True)
    sub_type = models.CharField(max_length=20, choices=SUB_TYPE_CHOICES, blank=True)
    size = models.CharField(max_length=100)
    length = models.CharField(max_length=50, choices=LENGTH_CHOICES, blank=True)
    pieces = models.IntegerField(null=True, blank=True)
    SITE_CHOICES = [
        ('site_1', 'Site 1'),
        ('site_2', 'Site 2'),
    ]

    grade = models.CharField(max_length=50, choices=GRADE_CHOICES, blank=True)
    godown = models.CharField(max_length=100, blank=True)
    site = models.CharField(max_length=10, choices=SITE_CHOICES, blank=True)
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
        ordering = ['category', 'sub_type', 'size']

    def __str__(self):
        parts = [self.hsn_code, self.get_sub_type_display() or self.get_category_display(), self.size]
        if self.length:
            parts.append(self.length)
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
