from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'employee_id', 'get_full_name', 'role', 'branch', 'is_active')
    list_filter = ('role', 'branch', 'is_active')
    search_fields = ('username', 'first_name', 'last_name', 'employee_id')
    fieldsets = UserAdmin.fieldsets + (
        ('Staff Info', {'fields': ('role', 'team', 'phone', 'phone_2', 'employee_id', 'branch')}),
    )

    class Media:
        js = ('admin/js/user_role_filter.js',)
