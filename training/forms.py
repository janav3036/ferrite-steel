from django import forms
from database.models import Customer
from .models import QuizSet, Question, Case, KnowledgeDocument

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

class QuizSetForm(forms.ModelForm):
    departments = forms.MultipleChoiceField(
        choices=DEPARTMENT_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )

    class Meta:
        model = QuizSet
        fields = ['title', 'description', 'departments']


class QuestionForm(forms.ModelForm):
    departments = forms.MultipleChoiceField(
        choices=DEPARTMENT_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )

    class Meta:
        model = Question
        fields = ['quiz_set', 'question_text', 'correct_answer', 'source', 'departments']
        widgets = {
            'question_text': forms.Textarea(attrs={'rows': 3}),
            'correct_answer': forms.Textarea(attrs={'rows': 3}),
        }

class KnowledgeDocumentForm(forms.ModelForm):
    departments = forms.MultipleChoiceField(
        choices=DEPARTMENT_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False
        )
    file = forms.FileField(required=False)
    
    class Meta:
        model = KnowledgeDocument
        fields = ['title', 'source_type', 'departments', 'description', 'direct_text']
        widgets = {
            'description': forms.Textarea(attrs={'rows':2}),
            'direct_text': forms.Textarea(attrs={'rows':8}),
        }
