from django.contrib import admin
from .models import HazardRegistry, RiskAssessment, ControlMeasure, ActionPlan


@admin.register(HazardRegistry)
class HazardRegistryAdmin(admin.ModelAdmin):
    list_display = ['descricao_perigo', 'company', 'setor', 'tipo_risco', 'norma_referencia', 'status']
    list_filter = ['tipo_risco', 'norma_referencia', 'status', 'company']
    search_fields = ['descricao_perigo', 'setor', 'funcao']


@admin.register(RiskAssessment)
class RiskAssessmentAdmin(admin.ModelAdmin):
    list_display = ['hazard', 'probabilidade', 'severidade', 'score', 'nivel_risco', 'data_avaliacao']
    list_filter = ['nivel_risco']


@admin.register(ControlMeasure)
class ControlMeasureAdmin(admin.ModelAdmin):
    list_display = ['descricao', 'tipo', 'responsavel', 'implementada', 'eficacia_verificada']
    list_filter = ['tipo', 'implementada']


@admin.register(ActionPlan)
class ActionPlanAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'company', 'status', 'prioridade', 'prazo_fim', 'percentual_conclusao']
    list_filter = ['status', 'prioridade', 'company']
    search_fields = ['titulo', 'responsavel']
