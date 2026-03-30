"""
Configuracao do Django Admin para auditoria.
"""
from django.contrib import admin
from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """Admin para logs de auditoria (somente leitura)."""
    
    list_display = ['created_at', 'user', 'action', 'description_short', 'company', 'ip_address']
    list_filter = ['action', 'company', 'created_at']
    search_fields = ['description', 'user__email', 'ip_address']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    
    readonly_fields = [
        'user', 'company', 'action', 'description',
        'content_type', 'object_id', 'ip_address',
        'user_agent', 'extra_data', 'created_at'
    ]
    
    def description_short(self, obj):
        return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
    description_short.short_description = 'Descricao'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
