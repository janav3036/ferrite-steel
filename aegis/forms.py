from django.contrib.auth.forms import UserCreationForm
from django.forms import ModelForm
from .models import CustomUser


class AddUserForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = [
            'username', 'first_name', 'last_name', 'email',
            'team', 'role', 'phone', 'branch', 'employee_id',
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
            'phone', 'branch', 'employee_id',
            'password1', 'password2',
        ]