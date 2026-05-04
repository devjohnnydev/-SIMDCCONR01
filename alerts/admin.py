from django.contrib import admin
from .models import Alert


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'company', 'tipo', 'severidade', 'is_read', 'is_resolved', 'created_at']
    list_filter = ['tipo', 'severidade', 'is_read', 'is_resolved', 'company']
    search_fields = ['titulo', 'mensagem']
