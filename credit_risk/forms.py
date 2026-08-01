from django import forms

from database.models import Customer


class CreditAssessmentRequestForm(forms.Form):
    customer = forms.ModelChoiceField(queryset=Customer.objects.none())
    notes = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
        required=True,
        help_text='Payment behaviour, disputes, relationship history — anything not in the Tally export.',
    )
    trading_file = forms.FileField(required=True, label='Tally Export (.xlsx)')

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user and user.role == 'lead' and user.team:
            self.fields['customer'].queryset = Customer.objects.filter(handling_team=user.team)
        else:
            self.fields['customer'].queryset = Customer.objects.all()

    def clean_trading_file(self):
        f = self.cleaned_data['trading_file']
        if not f.name.lower().endswith(('.xlsx', '.xls')):
            raise forms.ValidationError('Please upload an Excel file (.xlsx or .xls).')
        return f