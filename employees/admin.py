"""
Configuracao do Django Admin para funcionarios.
"""
from django.contrib import admin
from .models import Employee, EmployeeImportLog


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    """Admin para gestao de funcionarios."""
    
    list_display = ['nome', 'email', 'company', 'setor', 'cargo', 'status', 'data_admissao']
    list_filter = ['status', 'company', 'setor', 'turno']
    search_fields = ['nome', 'email', 'cpf', 'cargo']
    ordering = ['nome']
    
    fieldsets = (
        ('Dados Pessoais', {
            'fields': ('nome', 'email', 'cpf', 'data_nascimento')
        }),
        ('Empresa e Cargo', {
            'fields': ('company', 'setor', 'cargo', 'turno', 'matricula', 'gestor')
        }),
        ('Status', {
            'fields': ('status', 'data_admissao', 'user')
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']


@admin.register(EmployeeImportLog)
class EmployeeImportLogAdmin(admin.ModelAdmin):
    """Admin para logs de importacao."""
    
    list_display = ['file_name', 'company', 'status', 'success_count', 'error_count', 'created_at']
    list_filter = ['status', 'company', 'created_at']
    readonly_fields = ['company', 'file_name', 'status', 'total_rows', 'success_count', 'error_count', 'errors', 'created_at', 'created_by']
