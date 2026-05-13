from django.contrib import admin
from .models import Lead, MarketOrder, Quotation, QuotationLineItem


class QuotationLineItemInline(admin.TabularInline):
    model = QuotationLineItem
    extra = 0


@admin.register(MarketOrder)
class MarketOrderAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'sub_team', 'status', 'rate', 'do_number', 'created_by', 'created_at')
    list_filter = ('status', 'sub_team')
    search_fields = ('broker__name', 'do_number')


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer_name', 'source', 'status', 'created_by', 'created_at')
    list_filter = ('source', 'status')
    search_fields = ('customer_name', 'customer_phone', 'customer_email')


@admin.register(Quotation)
class QuotationAdmin(admin.ModelAdmin):
    list_display = ('quotation_number', 'lead', 'status', 'total_amount', 'created_by', 'created_at')
    list_filter = ('status',)
    inlines = [QuotationLineItemInline]
