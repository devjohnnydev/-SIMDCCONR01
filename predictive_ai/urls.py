"""URLs para IA Preditiva."""
from django.urls import path
from . import views

app_name = 'predictive_ai'

urlpatterns = [
    path('', views.predictive_dashboard, name='dashboard'),
    path('acknowledge/<int:pk>/', views.acknowledge_alert, name='acknowledge'),
    path('run-analysis/', views.run_analysis_manual, name='run_analysis'),
    path('api/suggestions/', views.suggestions_api, name='suggestions_api'),
    path('suggestions/', views.suggestion_list, name='suggestion_list'),
]
