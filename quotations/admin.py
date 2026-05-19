from django.contrib import admin
from .models import Lead, MarketOrder, ProductKeyword, Quotation, QuotationLineItem, TeamEmailConfig


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
    list_display = ('quotation_number', 'lead', 'status', 'outcome', 'winning_quotation', 'stock_deducted', 'total_amount', 'created_by', 'created_at')
    list_filter = ('status', 'outcome', 'stock_deducted')
    readonly_fields = ('winning_quotation', 'stock_deducted')
    inlines = [QuotationLineItemInline]


@admin.register(ProductKeyword)
class ProductKeywordAdmin(admin.ModelAdmin):
    list_display  = ('keyword', 'maps_to', 'notes', 'is_active')
    list_filter   = ('is_active',)
    search_fields = ('keyword', 'maps_to')
    list_editable = ('is_active',)


@admin.register(TeamEmailConfig)
class TeamEmailConfigAdmin(admin.ModelAdmin):
    list_display  = ('get_team_display', 'email_address', 'imap_host', 'is_active')
    list_filter   = ('is_active', 'team')
    list_editable = ('is_active',)
