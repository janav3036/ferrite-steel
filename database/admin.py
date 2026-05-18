from django.contrib import admin
from .models import Broker, Customer, Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('hsn_code', 'make', 'sub_type', 'size', 'length', 'grade', 'godown', 'site', 'quantity', 'rate', 'is_active')
    list_filter = ('make', 'sub_type', 'site', 'is_active')
    search_fields = ('hsn_code', 'size', 'grade')


@admin.register(Broker)
class BrokerAdmin(admin.ModelAdmin):
    list_display = ('name', 'company', 'phone', 'location', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'company')


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('customer_code', 'name', 'company', 'handling_team', 'gst_number', 'payment_terms', 'transport_extra', 'loading_rate', 'updated_at')
    list_filter = ('handling_team', 'payment_terms')
    search_fields = ('customer_code', 'name', 'company', 'gst_number')
    fields = (
        'customer_code', 'name', 'company', 'phone', 'email',
        'gst_number', 'billing_address', 'shipping_address',
        'payment_terms', 'transport_extra', 'loading_rate',
        'handling_team', 'notes', 'competitors',
    )
