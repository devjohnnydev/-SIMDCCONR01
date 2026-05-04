from django.contrib import admin
from .models import PredictiveAlert, NRSuggestion


@admin.register(PredictiveAlert)
class PredictiveAlertAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'company', 'trend_type', 'confidence', 'setor', 'is_acknowledged', 'created_at']
    list_filter = ['trend_type', 'confidence', 'is_acknowledged', 'company']
    search_fields = ['titulo', 'descricao', 'setor']


@admin.register(NRSuggestion)
class NRSuggestionAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'tipo_risco', 'nivel_risco_minimo', 'norma_referencia', 'categoria', 'prioridade', 'is_active']
    list_filter = ['tipo_risco', 'categoria', 'norma_referencia', 'is_active']
    search_fields = ['titulo', 'descricao']
