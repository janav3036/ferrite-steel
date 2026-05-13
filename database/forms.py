from django import forms
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
    class Meta:
        model = Customer
        fields = [
            'name', 'company', 'location', 'phone', 'email',
            'transport_extra', 'loading_rate', 'handling_team', 'notes',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'company': forms.TextInput(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'transport_extra': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'loading_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'handling_team': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        labels = {'notes': 'Notes (AI context)', 'transport_extra': 'Transport Extra (₹)', 'loading_rate': 'Loading Rate (₹/T)'}


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'hsn_code', 'size', 'length', 'type', 'sub_type',
            'pieces', 'grade', 'location', 'quantity', 'rate', 'is_active',
        ]
        widgets = {
            'hsn_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 72141000'}),
            'size': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 12mm'}),
            'length': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 12 mtr, 4 to 5 mtr'}),
            'type': forms.Select(attrs={'class': 'form-select', 'id': 'id_type'}),
            'sub_type': forms.Select(attrs={'class': 'form-select', 'id': 'id_sub_type'}),
            'pieces': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Leave blank if N/A'}),
            'grade': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Fe500D'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Plot 557'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}),
            'rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {'length': 'Length (m)'}
