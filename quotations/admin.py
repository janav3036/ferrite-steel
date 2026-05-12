from django.contrib import admin
from .models import Broker, Customer, Lead, MarketOrder, PricingEntry, Quotation, QuotationLineItem


class QuotationLineItemInline(admin.TabularInline):
    model = QuotationLineItem
    extra = 0


@admin.register(Broker)
class BrokerAdmin(admin.ModelAdmin):
    list_display = ('name', 'company', 'phone', 'location', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'company')


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'company', 'location', 'transport_extra', 'loading_rate', 'updated_at')
    search_fields = ('name', 'company')
    fields = ('name', 'company', 'location', 'phone', 'email',
              'transport_extra', 'loading_rate', 'notes')


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
