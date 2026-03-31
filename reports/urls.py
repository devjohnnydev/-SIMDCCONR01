"""
URLs para relatorios.
"""
from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.report_list, name='list'),
    path('dashboard/', views.report_dashboard, name='dashboard'),
    path('form/<int:form_pk>/pdf/', views.generate_form_report, name='form_pdf'),
    path('period/', views.generate_period_report, name='period_pdf'),
    path('validar/', views.validate_diagnostic, name='validate'),
    path('validar/<str:validation_code>/', views.validate_diagnostic, name='validate_code'),
    path('laudo/<str:validation_code>/', views.view_diagnostic, name='view_diagnostic'),
]
