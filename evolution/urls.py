"""URLs para Evolução e Inteligência."""
from django.urls import path
from . import views

app_name = 'evolution'

urlpatterns = [
    path('', views.evolution_dashboard, name='dashboard'),
    path('compare/<int:snapshot_a>/<int:snapshot_b>/', views.compare_snapshots, name='compare'),
    path('risk-score/', views.risk_score_timeline, name='risk_score'),
    path('dimension/<str:instrumento>/<str:dimensao>/', views.dimension_detail, name='dimension_detail'),
    path('api/chart-data/<int:company_pk>/', views.chart_data_api, name='chart_data_api'),

    # Evolução por setor
    path('setores/', views.sector_evolution, name='sector_evolution'),

    # Evolução individual de funcionário
    path('individual/', views.employee_evolution, name='employee_evolution'),
    path('individual/<int:employee_pk>/', views.employee_evolution, name='employee_evolution_detail'),

    # Visão consolidada (Admin Master)
    path('todas-empresas/', views.all_companies_evolution, name='all_companies'),
]
