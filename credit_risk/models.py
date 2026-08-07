from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

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