"""
Configuracao do Django Admin para usuarios.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin customizado para o modelo User."""
    
    list_display = ['email', 'first_name', 'last_name', 'role', 'company', 'is_active', 'date_joined']
    list_filter = ['role', 'is_active', 'is_staff', 'company']
    search_fields = ['email', 'first_name', 'last_name']
    ordering = ['-date_joined']
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Informacoes Pessoais', {'fields': ('first_name', 'last_name')}),
        ('Empresa e Papel', {'fields': ('company', 'role')}),
        ('Permissoes', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('LGPD - Consentimentos', {'fields': ('lgpd_individual_accepted', 'lgpd_individual_at', 'lgpd_aggregate_accepted', 'lgpd_aggregate_at')}),
        ('Datas', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'role', 'company', 'password1', 'password2'),
        }),
    )
    
    readonly_fields = ['date_joined', 'last_login', 'lgpd_individual_at', 'lgpd_aggregate_at']
