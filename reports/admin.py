"""
Configuracao do Django Admin para relatorios.
"""
from django.contrib import admin
from .models import Report


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    """Admin para relatorios."""
    
    list_display = ['title', 'company', 'report_type', 'created_at', 'created_by']
    list_filter = ['report_type', 'company', 'created_at']
    search_fields = ['title', 'description']
    ordering = ['-created_at']
    
    readonly_fields = ['created_at', 'created_by', 'results_data']
