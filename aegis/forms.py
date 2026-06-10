from django.contrib.auth.forms import UserCreationForm
from django.forms import ModelForm
import django.forms as forms
from .models import CustomUser


class AddUserForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = [
            'username', 'first_name', 'last_name', 'email',
            'team', 'role', 'phone', 'phone_2', 'branch', 'employee_id',
            'password1', 'password2',
        ]


class EditRoleForm(ModelForm):
    class Meta:
        model = CustomUser
        fields = ['team', 'role']

class RegistrationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = [
            'username', 'first_name', 'last_name', 'email',
            'phone', 'phone_2', 'branch', 'employee_id',
            'password1', 'password2',
        ]


class ProfileForm(ModelForm):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'phone', 'phone_2', 'branch']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name':  forms.TextInput(attrs={'class': 'form-control'}),
            'email':      forms.EmailInput(attrs={'class': 'form-control'}),
            'phone':      forms.TextInput(attrs={'class': 'form-control'}),
            'phone_2':    forms.TextInput(attrs={'class': 'form-control'}),
            'branch':     forms.TextInput(attrs={'class': 'form-control'}),
        }