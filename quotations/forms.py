from django import forms
from django.forms import inlineformset_factory
from .models import Broker, Lead, MarketOrder, Quotation, QuotationLineItem


class ManualLeadForm(forms.ModelForm):
    class Meta:
        model = Lead
        fields = [
            'customer_name', 'customer_phone', 'customer_email',
            'company', 'industry', 'location',
            'broker', 'raw_text', 'notes',
        ]
        widgets = {
            'customer_name': forms.TextInput(attrs={'class': 'form-control'}),
            'customer_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'customer_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'company': forms.TextInput(attrs={'class': 'form-control'}),
            'industry': forms.TextInput(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'broker': forms.Select(attrs={'class': 'form-select'}),
            'raw_text': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Paste or type the enquiry here…',
            }),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        labels = {
            'raw_text': 'Enquiry Text',
            'broker': 'Broker (Market team only)',
        }


class QuotationEditForm(forms.ModelForm):
    class Meta:
        model = Quotation
        fields = ['payment_terms', 'delivery_address', 'transport_extra', 'sgst_percent', 'cgst_percent', 'notes', 'valid_until']
        widgets = {
            'payment_terms': forms.TextInput(attrs={'class': 'form-control'}),
            'delivery_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'transport_extra': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'sgst_percent': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'cgst_percent': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'valid_until': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }


class LineItemForm(forms.ModelForm):
    class Meta:
        model = QuotationLineItem
        fields = ['product_name', 'make', 'length', 'pcs', 'quantity', 'unit_price', 'total_price', 'notes']
        widgets = {
            'product_name': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'make': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'length': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'step': '0.01'}),
            'pcs': forms.NumberInput(attrs={'class': 'form-control form-control-sm'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'step': '0.001'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'step': '0.01'}),
            'total_price': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'readonly': True}),
            'notes': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
        }


LineItemFormSet = inlineformset_factory(
    Quotation,
    QuotationLineItem,
    form=LineItemForm,
    extra=1,
    can_delete=True,
)


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


class MarketOrderForm(forms.ModelForm):
    class Meta:
        model = MarketOrder
        fields = ['broker', 'sub_team', 'product_details', 'quantity', 'notes']
        widgets = {
            'broker': forms.Select(attrs={'class': 'form-select'}),
            'sub_team': forms.Select(attrs={'class': 'form-select'}),
            'product_details': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class MarketOrderRateForm(forms.ModelForm):
    class Meta:
        model = MarketOrder
        fields = ['rate']
        widgets = {
            'rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }


class MarketOrderAssignForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from aegis.models import CustomUser
        self.fields['loading_dock_member'].queryset = CustomUser.objects.filter(
            role='loading_dock', is_active=True
        )

    class Meta:
        model = MarketOrder
        fields = ['loading_dock_member']
        widgets = {
            'loading_dock_member': forms.Select(attrs={'class': 'form-select'}),
        }


class MarketOrderDOForm(forms.ModelForm):
    class Meta:
        model = MarketOrder
        fields = ['do_number']
        widgets = {
            'do_number': forms.TextInput(attrs={'class': 'form-control'}),
        }
