from django import forms

from database.models import Customer


class CreditAssessmentRequestForm(forms.Form):
    customer = forms.ModelChoiceField(queryset=Customer.objects.none())
    notes = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
        required=True,
        help_text='Payment behaviour, disputes, relationship history — anything not in the Tally export.',
    )
    trading_file = forms.FileField(required=True, label="Customer's Own Tally Export (.xlsx)")

    # Admin-only, per-assessment override of CreditScoringConfig's default
    # marks for this one run — global rebalancing belongs in Django admin,
    # this is for a one-off exception on a single customer.
    override_competitor_max = forms.FloatField(
        required=False, min_value=0, label='Competitor marks (override)',
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5'}),
    )
    override_concentration_max = forms.FloatField(
        required=False, min_value=0, label="Customer's-customer marks (override)",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5'}),
    )
    override_turnover_max = forms.FloatField(
        required=False, min_value=0, label='Turnover marks (override)',
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5'}),
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_admin = bool(user and user.role == 'admin')
        if not self.is_admin:
            for name in ('override_competitor_max', 'override_concentration_max', 'override_turnover_max'):
                del self.fields[name]
        if user and user.role == 'lead' and user.team:
            self.fields['customer'].queryset = Customer.objects.filter(handling_team=user.team)
        else:
            self.fields['customer'].queryset = Customer.objects.all()

    def clean_trading_file(self):
        f = self.cleaned_data['trading_file']
        if not f.name.lower().endswith(('.xlsx', '.xls')):
            raise forms.ValidationError('Please upload an Excel file (.xlsx or .xls).')
        return f

    def weight_overrides(self):
        if not self.is_admin:
            return None
        data = self.cleaned_data
        overrides = {}
        field_to_key = {
            'override_competitor_max': 'competitor_max',
            'override_concentration_max': 'concentration_max',
            'override_turnover_max': 'turnover_max',
        }
        for field_name, key in field_to_key.items():
            value = data.get(field_name)
            if value is not None:
                overrides[key] = value
        return overrides or None
