"""
Configuracao do Django Admin para billing.
"""
from django.contrib import admin
from .models import Plan, Subscription, PaymentOrder, CustomPlanRequest


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    """Admin para planos."""
    
    list_display = ['name', 'pricing_mode', 'price_monthly', 'base_price', 'per_employee_price', 'max_employees', 'is_active', 'is_featured', 'order']
    list_filter = ['is_active', 'is_featured']
    search_fields = ['name', 'description']
    ordering = ['order']
    
    fieldsets = (
        ('Informacoes Basicas', {
            'fields': ('name', 'description', 'order')
        }),
        ('Pricing Fixo', {
            'fields': ('price_monthly', 'price_yearly', 'price_semestral')
        }),
        ('Pricing Dinâmico', {
            'fields': ('pricing_mode', 'base_price', 'per_employee_price',
                       'min_employees_discount', 'discount_pct_small', 'discount_pct_corporate',
                       'default_billing_cycle'),
            'description': 'Configurações para cálculo automático baseado em funcionários.'
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
    
    list_display = ['company', 'plan', 'status', 'billing_cycle', 'calculated_price', 'start_date', 'end_date']
    list_filter = ['status', 'plan', 'billing_cycle']
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


@admin.register(CustomPlanRequest)
class CustomPlanRequestAdmin(admin.ModelAdmin):
    """Admin para solicitacoes de planos personalizados."""
    
    list_display = ['company', 'status', 'created_at', 'proposed_price_monthly']
    list_filter = ['status', 'has_pdf_export', 'has_api_access']
    search_fields = ['company__nome_fantasia']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Empresa e Status', {
            'fields': ('company', 'status')
        }),
        ('Recursos Solicitados', {
            'fields': ('max_employees', 'max_forms', 'max_reports', 'data_retention_days', 
                       'has_pdf_export', 'has_csv_import', 'has_api_access', 'has_custom_branding', 'has_priority_support')
        }),
        ('Proposta Admin', {
            'fields': ('proposed_price_monthly', 'proposed_price_yearly', 'admin_message')
        }),
        ('Comunicacao Empresa', {
            'fields': ('user_message',)
        }),
        ('Metadados', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
