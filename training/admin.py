from django.contrib import admin
from .models import Case

@admin.register(Case)
class CaseAdmin(admin.ModelAdmin):
    list_display = ('title', 'customer', 'created_by', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('title', 'problem_description')
    readonly_fields = ('created_at',)