from django import forms
from .models import Lead


class ManualLeadForm(forms.ModelForm):
    class Meta:
        model = Lead
        fields = ['customer_name', 'customer_phone', 'customer_email', 'raw_text', 'notes']
        widgets = {
            'customer_name': forms.TextInput(attrs={'class': 'form-control'}),
            'customer_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'customer_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'raw_text': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Paste or type the enquiry here…',
            }),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        labels = {
            'raw_text': 'Enquiry Text',
        }
