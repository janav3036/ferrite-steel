from django import forms
from django.forms import inlineformset_factory
from database.models import Broker
from .models import Lead, MarketOrder, Quotation, QuotationLineItem


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
        fields = ['payment_terms', 'delivery_address', 'loading_extra', 'transport_extra', 'sgst_percent', 'cgst_percent', 'notes', 'valid_until']
        widgets = {
            'payment_terms': forms.Select(attrs={'class': 'form-select'}),
            'delivery_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'loading_extra': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'transport_extra': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'sgst_percent': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'cgst_percent': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'valid_until': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }


class LineItemForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['product'].required = False

    class Meta:
        model = QuotationLineItem
        fields = ['product', 'hsn_code', 'product_name', 'make', 'length', 'quantity', 'uom', 'pcs', 'unit_price', 'total_price', 'discount_pct', 'notes']
        widgets = {
            'product': forms.HiddenInput(),
            'hsn_code': forms.TextInput(attrs={'class': 'form-control form-control-sm', 'readonly': 'readonly', 'tabindex': '-1'}),
            'product_name': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'make': forms.TextInput(attrs={'class': 'form-control form-control-sm', 'readonly': True}),
            'length': forms.TextInput(attrs={'class': 'form-control form-control-sm', 'readonly': True}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control form-control-sm qty-field', 'step': '0.001', 'style': 'width:75px'}),
            'uom': forms.Select(attrs={'class': 'form-select form-select-sm uom-field', 'style': 'width:58px;flex:0 0 auto'}),
            'pcs': forms.NumberInput(attrs={'class': 'form-control form-control-sm'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control form-control-sm final-rate-field', 'readonly': True, 'tabindex': '-1', 'step': '0.01'}),
            'total_price': forms.NumberInput(attrs={'class': 'form-control form-control-sm amt-field', 'readonly': True}),
            'discount_pct': forms.NumberInput(attrs={'class': 'form-control form-control-sm discount-pct-field', 'step': '0.01', 'placeholder': '0', 'style': 'width:70px'}),
            'notes': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
        }


LineItemFormSet = inlineformset_factory(
    Quotation,
    QuotationLineItem,
    form=LineItemForm,
    extra=1,
    can_delete=True,
)


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
