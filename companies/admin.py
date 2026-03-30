"""
Configuracao do Django Admin para empresas.
"""
from django.contrib import admin
from django.utils import timezone
from .models import Company, Announcement


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    """Admin para gestao de empresas."""
    
    list_display = ['nome_fantasia', 'cnpj', 'status', 'plan', 'created_at', 'approved_at']
    list_filter = ['status', 'plan', 'created_at']
    search_fields = ['nome_fantasia', 'razao_social', 'cnpj', 'responsavel_email']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Dados da Empresa', {
            'fields': ('nome_fantasia', 'razao_social', 'cnpj')
        }),
        ('Responsavel', {
            'fields': ('responsavel_nome', 'responsavel_email', 'telefone')
        }),
        ('Endereco', {
            'fields': ('endereco', 'cidade', 'estado', 'cep'),
            'classes': ('collapse',)
        }),
        ('Personalizacao', {
            'fields': ('logo', 'cor_primaria', 'cor_secundaria')
        }),
        ('Status e Plano', {
            'fields': ('status', 'plan')
        }),
        ('Aprovacao', {
            'fields': ('approved_at', 'approved_by'),
            'classes': ('collapse',)
        }),
        ('Configuracoes', {
            'fields': ('configs',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at', 'approved_at', 'approved_by']
    
    actions = ['approve_companies', 'suspend_companies']
    
    def approve_companies(self, request, queryset):
        """Acao para aprovar empresas selecionadas."""
        count = 0
        for company in queryset.filter(status='PENDING'):
            company.approve(request.user)
            count += 1
        self.message_user(request, f'{count} empresa(s) aprovada(s).')
    approve_companies.short_description = 'Aprovar empresas selecionadas'
    
    def suspend_companies(self, request, queryset):
        """Acao para suspender empresas selecionadas."""
        count = queryset.filter(status='ACTIVE').update(status='SUSPENDED')
        self.message_user(request, f'{count} empresa(s) suspensa(s).')
    suspend_companies.short_description = 'Suspender empresas selecionadas'


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    """Admin para comunicados."""
    
    list_display = ['title', 'company', 'is_active', 'created_at', 'created_by']
    list_filter = ['is_active', 'company', 'created_at']
    search_fields = ['title', 'content']
