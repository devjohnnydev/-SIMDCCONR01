"""
URLs para relatorios.
"""
from django.urls import path
from . import views, debug_views

app_name = 'reports'

urlpatterns = [
    path('', views.report_list, name='list'),
    path('dashboard/', views.report_dashboard, name='dashboard'),
    path('dashboard/company/<int:company_pk>/', views.admin_company_dashboard, name='admin_dashboard'),
    path('form/<int:form_pk>/pdf/', views.generate_form_report, name='form_pdf'),
    path('period/', views.generate_period_report, name='period_pdf'),
    path('validar/', views.validate_diagnostic, name='validate'),
    path('validar/<str:validation_code>/', views.validate_diagnostic, name='validate_code'),
    path('laudo/<str:validation_code>/', views.view_diagnostic, name='view_diagnostic'),
    path('laudo/<str:validation_code>/pdf/', views.download_diagnostic_pdf, name='diagnostic_pdf'),
    path('laudo/<str:validation_code>/sign/', views.sign_report, name='sign_report'),

    # Motor de Texto — Gerador Automático (SIMDCCONR01)
    # Nível 1: Devolutiva Individual (Respondente)
    path('simdcconr01/<int:form_pk>/individual/<int:assignment_pk>/pdf/',
         views.download_individual_pdf, name='individual_pdf'),

    # Nível 1.5: Anexo PCMSO (Individual Obrigatório)
    path('simdcconr01/<int:form_pk>/pcmso/<int:assignment_pk>/pdf/',
         views.download_pcmso_pdf, name='pcmso_pdf'),

    # Nível 3: Laudo Pericial Organizacional
    path('simdcconr01/<int:form_pk>/organizacional/pdf/',
         views.download_organizational_pdf, name='organizational_pdf'),

    # Legacy: rota original do laudo integrado (agora usa Motor de Texto)
    path('simdcconr01/<int:form_pk>/pdf/',
         views.generate_simdcconr01_report, name='simdcconr01_pdf'),
    
    # Debug & Diagnóstico (Apenas Admin Master)
    path('debug/system/', debug_views.system_diagnostics, name='system_diagnostics'),
]

