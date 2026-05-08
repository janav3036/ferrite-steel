from django.contrib import admin
from .models import Lead, PricingEntry, Quotation, QuotationLineItem


class QuotationLineItemInline(admin.TabularInline):
    model = QuotationLineItem
    extra = 0


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer_name', 'source', 'status', 'created_by', 'created_at')
    list_filter = ('source', 'status')
    search_fields = ('customer_name', 'customer_phone', 'customer_email')


@admin.register(PricingEntry)
class PricingEntryAdmin(admin.ModelAdmin):
    list_display = ('product_code', 'product_name', 'category', 'unit', 'base_price', 'is_active')
    list_filter = ('category', 'is_active')
    search_fields = ('product_code', 'product_name')


@admin.register(Quotation)
class QuotationAdmin(admin.ModelAdmin):
    list_display = ('quotation_number', 'lead', 'status', 'total_amount', 'created_by', 'created_at')
    list_filter = ('status',)
    inlines = [QuotationLineItemInline]
