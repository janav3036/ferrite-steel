from django import forms
from .models import Case
from database.models import Customer

DEPARTMENT_CHOICES = [
    ('team_9', 'Team 9'),
    ('cs', 'CS Team'),
    ('market', 'Market Team'),
    ('corporate', 'Corporate Team'),
]


class CaseForm(forms.ModelForm):
    departments = forms.MultipleChoiceField(
        choices=DEPARTMENT_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )
    customer = forms.ModelChoiceField(
        queryset=Customer.objects.filter(is_active=True).order_by('name'),
        required=False,
        empty_label='— No customer —',
    )

    class Meta:
        model = Case
        fields = ['title', 'problem_description', 'context', 'resolution', 'departments', 'customer']
        widgets = {
            'problem_description': forms.Textarea(attrs={'rows': 4}),
            'context': forms.Textarea(attrs={'rows': 3}),
            'resolution': forms.Textarea(attrs={'rows': 4}),
        }
