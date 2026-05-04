from django.contrib import admin
from .models import EvolutionSnapshot, RiskScoreHistory, DimensionEvolution


@admin.register(EvolutionSnapshot)
class EvolutionSnapshotAdmin(admin.ModelAdmin):
    list_display = ['company', 'snapshot_date', 'overall_score', 'overall_classification', 'total_respondentes']
    list_filter = ['overall_classification', 'company']


@admin.register(RiskScoreHistory)
class RiskScoreHistoryAdmin(admin.ModelAdmin):
    list_display = ['company', 'date', 'score', 'faixa']
    list_filter = ['faixa', 'company']


@admin.register(DimensionEvolution)
class DimensionEvolutionAdmin(admin.ModelAdmin):
    list_display = ['company', 'instrumento', 'dimensao', 'media', 'classificacao', 'date']
    list_filter = ['instrumento', 'company']
