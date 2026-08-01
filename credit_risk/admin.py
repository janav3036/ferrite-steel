from django.contrib import admin

from .models import CreditAssessment


@admin.register(CreditAssessment)
class CreditAssessmentAdmin(admin.ModelAdmin):
    list_display = ('customer', 'score', 'risk_level', 'recommendation', 'requested_by', 'created_at')
    list_filter = ('risk_level', 'recommendation')
    search_fields = ('customer__name', 'customer__company')
    readonly_fields = (
        'customer', 'requested_by', 'notes', 'trading_history', 'trading_history_source_filename',
        'score', 'risk_level', 'recommendation', 'summary', 'factors', 'llm_raw_response', 'created_at',
    )