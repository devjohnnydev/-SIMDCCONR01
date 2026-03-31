"""
Configuracao do Django Admin para relatorios.
"""
from django.contrib import admin
from .models import Report, EmployeeDiagnostic


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    """Admin para relatorios."""
    
    list_display = ['title', 'company', 'report_type', 'created_at', 'created_by']
    list_filter = ['report_type', 'company', 'created_at']
    search_fields = ['title', 'description']
    ordering = ['-created_at']
    
    readonly_fields = ['created_at', 'created_by', 'results_data']


@admin.register(EmployeeDiagnostic)
class EmployeeDiagnosticAdmin(admin.ModelAdmin):
    """Admin para laudos individuais IA."""
    
    list_display = ['validation_code', 'get_employee', 'generated_at']
    list_filter = ['generated_at']
    search_fields = ['validation_code', 'assignment__employee__nome']
    
    def get_employee(self, obj):
        return obj.assignment.employee.nome
    get_employee.short_description = 'Funcionário'
