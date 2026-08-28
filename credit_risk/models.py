from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


class ListedCompany(models.Model):
    """Reference data: NSE/BSE-listed companies, used to flag a customer's own
    top-tier buyers as publicly listed (informational signal, not a scored mark).
    Seeded via import_listed_companies.py; admin-editable after that."""
    EXCHANGE_CHOICES = [
        ('nse', 'NSE'),
        ('bse', 'BSE'),
        ('both', 'NSE & BSE'),
    ]
    name = models.CharField(max_length=255, unique=True)
    exchange = models.CharField(max_length=4, choices=EXCHANGE_CHOICES, default='nse')

    class Meta:
        verbose_name = 'Listed Company'
        verbose_name_plural = 'Listed Companies (NSE/BSE reference)'
        ordering = ['name']

    def __str__(self):
        return self.name


class CreditScoringConfig(models.Model):
    """Singleton (pk=1) holding the default marks-per-category used by the
    deterministic scoring formula in services/scoring.py. Admin-editable, so
    the client can rebalance the rubric (e.g. competitors 3 -> 5 marks)
    without a code change. A single CreditAssessment can still override these
    per-run via CreditAssessment.weight_overrides."""
    competitor_max = models.FloatField(default=3.0, help_text='Max marks for the Competitor Streak category.')
    concentration_max = models.FloatField(default=2.0, help_text="Max marks for the Customer's-Customer Concentration category.")
    turnover_max = models.FloatField(default=2.0, help_text='Max marks for the Sales Turnover category.')
    sales_vs_purchase_max = models.FloatField(default=2.0, help_text='Max marks for the Sales vs Purchases category (see sales_vs_purchase_active).')
    sales_vs_purchase_active = models.BooleanField(
        default=False,
        help_text='Sales vs Purchases is built but parked — client to confirm before counting it '
                  'toward the score. Leave off until then.',
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Credit Scoring Config'
        verbose_name_plural = 'Credit Scoring Config'

    def __str__(self):
        return 'Credit Scoring Weights'

    @classmethod
    def current(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class CreditAssessment(models.Model):
    RISK_LEVEL_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]

    RECOMMENDATION_CHOICES = [
        ('approve', 'Approve'),
        ('decline', 'Decline'),
        ('refer', 'Refer for Review'),
    ]

    CONFIDENCE_CHOICES = [
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    ]

    STATUS_CHOICES = [
        ('processing', 'Processing'),
        ('done', 'Done'),
        ('failed', 'Failed'),
    ]

    customer = models.ForeignKey(
        'database.customer', on_delete=models.CASCADE, related_name='credit_assessments',
    )
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='credit_assessments_requested'
    )
    notes = models.TextField(blank=True, help_text="Salesperson's free-text notes about the customer.")

    trading_history = models.JSONField(
        null=True, blank=True,
        help_text="Extracted per-sheet Tally data, plus company-wide and vendor-rank signals.",
    )
    trading_history_source_filename = models.CharField(max_length=255, blank=True)

    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default='processing')
    error_message = models.TextField(blank=True, help_text="Set when status=failed.")

    score = models.PositiveSmallIntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text='Derived from points_earned/points_possible (rounded to a 1-10 scale) — never set directly.',
    )
    points_earned = models.FloatField(null=True, blank=True, help_text='Deterministic marks awarded, from services/scoring.py.')
    points_possible = models.FloatField(null=True, blank=True, help_text='Deterministic marks possible, given the active categories/weights at assessment time.')
    score_breakdown = models.JSONField(
        default=list,
        help_text="[{'category', 'label', 'points', 'max', 'detail'}] — one entry per scoring category.",
    )
    weight_overrides = models.JSONField(
        null=True, blank=True,
        help_text='Per-assessment override of CreditScoringConfig maxes, if set at request time (admin only).',
    )
    risk_level = models.CharField(max_length=10, choices=RISK_LEVEL_CHOICES, blank=True)
    data_confidence = models.CharField(
        max_length=10, choices=CONFIDENCE_CHOICES, blank=True,
        help_text="How much evidence backed this score (match quality + notes + quotation history).",
    )
    recommendation = models.CharField(max_length=10, choices=RECOMMENDATION_CHOICES, blank=True)
    summary = models.TextField(blank=True)
    factors = models.JSONField(default=list, help_text="[{'factor', 'detail', 'impact'}]")
    llm_raw_response = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Credit Assessment'
        verbose_name_plural = 'Credit Assessments'
        ordering = ['-created_at']
        permissions = [
            ('can_request_credit_assessment', 'Can request credit assessment')
        ]

    def __str__(self):
        if self.status != 'done':
            return f'{self.customer} - {self.get_status_display()}'
        return f'{self.customer} - {self.get_risk_level_display()} ({self.score}/10)'