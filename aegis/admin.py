from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'employee_id', 'get_full_name', 'role', 'branch', 'is_active')
    list_filter = ('role', 'branch', 'is_active')
    search_fields = ('username', 'first_name', 'last_name', 'employee_id')
    fieldsets = UserAdmin.fieldsets + (
        ('Staff Info', {'fields': ('role', 'phone', 'employee_id', 'branch')}),
    )
