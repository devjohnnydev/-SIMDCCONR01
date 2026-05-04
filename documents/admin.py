from django.contrib import admin
from .models import Document, DocumentVersion


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'company', 'tipo', 'versao', 'status', 'validade', 'created_at']
    list_filter = ['tipo', 'status', 'company']
    search_fields = ['titulo', 'descricao']


@admin.register(DocumentVersion)
class DocumentVersionAdmin(admin.ModelAdmin):
    list_display = ['document', 'versao', 'alterado_por', 'alterado_em']
