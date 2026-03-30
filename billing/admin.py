"""
Configuracao do Django Admin para billing.
"""
from django.contrib import admin
from .models import Plan, Subscription


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    """Admin para planos."""
    
    list_display = ['name', 'price_monthly', 'max_employees', 'max_forms', 'is_active', 'is_featured', 'order']
    list_filter = ['is_active', 'is_featured']
    search_fields = ['name', 'description']
    ordering = ['order']
    
    fieldsets = (
        ('Informacoes Basicas', {
            'fields': ('name', 'description', 'order')
        }),
        ('Precos', {
            'fields': ('price_monthly', 'price_yearly')
        }),
        ('Limites', {
            'fields': ('max_employees', 'max_forms', 'max_reports', 'data_retention_days')
        }),
        ('Recursos', {
            'fields': ('has_pdf_export', 'has_csv_import', 'has_api_access', 'has_custom_branding', 'has_priority_support')
        }),
        ('Status', {
            'fields': ('is_active', 'is_featured')
        }),
    )


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """Admin para assinaturas."""
    
    list_display = ['company', 'plan', 'status', 'start_date', 'end_date', 'is_yearly']
    list_filter = ['status', 'plan', 'is_yearly']
    search_fields = ['company__nome_fantasia']
