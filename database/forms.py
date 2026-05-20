from django import forms
from django.contrib.auth import get_user_model
from .models import Broker, Customer, Product


class BrokerForm(forms.ModelForm):
    class Meta:
        model = Broker
        fields = ['name', 'company', 'phone', 'email', 'location', 'notes', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'company': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {'notes': 'Notes (AI context)'}


class CustomerForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        User = get_user_model()
        self.fields['rm'].queryset = User.objects.filter(is_active=True).order_by('first_name', 'username')
        self.fields['rm'].empty_label = '— Not assigned —'

    class Meta:
        model = Customer
        fields = [
            'customer_code', 'name', 'company', 'phone', 'email',
            'gst_number', 'billing_address', 'shipping_address',
            'payment_terms', 'transport_extra', 'loading_rate',
            'handling_team', 'rm', 'notes', 'competitors',
        ]
        widgets = {
            'customer_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. CUST-001'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'company': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'gst_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 27AABCU9603R1ZX'}),
            'billing_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'shipping_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'payment_terms': forms.Select(attrs={'class': 'form-select'}),
            'transport_extra': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'loading_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'handling_team': forms.Select(attrs={'class': 'form-select'}),
            'rm': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'competitors': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'One competitor per line'}),
        }
        labels = {
            'notes': 'Notes (AI context)',
            'transport_extra': 'Transport Extra (₹)',
            'loading_rate': 'Loading Rate (₹/T)',
            'competitors': 'Competitors',
            'rm': 'Relationship Manager',
        }


class ProductForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        qs = Product.objects.filter(base_product__isnull=True, is_active=True)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        self.fields['base_product'].queryset = qs
        self.fields['base_product'].empty_label = '— Standalone (no base product) —'

    class Meta:
        model = Product
        fields = [
            'hsn_code', 'size', 'category', 'sub_type', 'make',
            'length', 'grade', 'pieces', 'godown', 'site', 'quantity', 'rate',
            'base_product', 'rate_offset', 'is_active',
        ]
        widgets = {
            'hsn_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 72141000'}),
            'size': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 12mm'}),
            'category': forms.Select(attrs={'class': 'form-select', 'id': 'id_category'}),
            'sub_type': forms.Select(attrs={'class': 'form-select', 'id': 'id_sub_type'}),
            'make': forms.Select(attrs={'class': 'form-select'}),
            'length': forms.Select(attrs={'class': 'form-select'}),
            'grade': forms.Select(attrs={'class': 'form-select'}),
            'pieces': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Leave blank if N/A'}),
            'godown': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Plot 557'}),
            'site': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}),
            'rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'base_product': forms.Select(attrs={'class': 'form-select'}),
            'rate_offset': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'e.g. 3000'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'category': 'Category',
            'make': 'Make (Manufacturer)',
            'godown': 'Godown',
            'rate': 'Rate (₹/T) — direct rate; ignored if Base Product is set',
            'base_product': 'Base Product',
            'rate_offset': 'Rate Offset (₹/T)',
        }
