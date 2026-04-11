"""
Configuracao do Django Admin para billing.
"""
from django.contrib import admin
from .models import Plan, Subscription, PaymentOrder


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


@admin.register(PaymentOrder)
class PaymentOrderAdmin(admin.ModelAdmin):
    """Admin para ordens de pagamento."""
    
    list_display = ['id', 'company', 'plan', 'status', 'amount_display', 'is_yearly', 'created_at', 'paid_at']
    list_filter = ['status', 'plan', 'is_yearly']
    search_fields = ['company__nome_fantasia', 'stripe_session_id', 'stripe_payment_intent_id']
    readonly_fields = ['stripe_session_id', 'stripe_payment_intent_id', 'created_at', 'paid_at']
    ordering = ['-created_at']
    
    def amount_display(self, obj):
        return f"R$ {obj.amount / 100:.2f}"
    amount_display.short_description = 'Valor'
