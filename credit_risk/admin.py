from django.contrib import admin

from .models import CreditAssessment, CreditScoringConfig, ListedCompany


@admin.register(CreditAssessment)
class CreditAssessmentAdmin(admin.ModelAdmin):
    list_display = (
        'customer', 'status', 'points_earned', 'points_possible', 'score',
        'risk_level', 'recommendation', 'requested_by', 'created_at',
    )
    list_filter = ('status', 'risk_level', 'recommendation')
    search_fields = ('customer__name', 'customer__company')
    readonly_fields = (
        'customer', 'requested_by', 'notes', 'trading_history', 'trading_history_source_filename',
        'status', 'error_message', 'score', 'points_earned', 'points_possible', 'score_breakdown',
        'weight_overrides', 'risk_level', 'recommendation', 'summary', 'factors',
        'llm_raw_response', 'created_at',
    )


@admin.register(CreditScoringConfig)
class CreditScoringConfigAdmin(admin.ModelAdmin):
    """Singleton — the client's global marking-scheme weights. Edit the one
    existing row rather than adding a second; a per-assessment override is
    also available on the assessment-create form for one-off exceptions."""
    list_display = (
        'competitor_max', 'concentration_max', 'turnover_max',
        'sales_vs_purchase_max', 'sales_vs_purchase_active', 'updated_at',
    )

    def has_add_permission(self, request):
        return not CreditScoringConfig.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ListedCompany)
class ListedCompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'exchange')
    list_filter = ('exchange',)
    search_fields = ('name',)
