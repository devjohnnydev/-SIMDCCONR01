"""URLs para Gestão de Riscos (GRO)."""
from django.urls import path
from . import views

app_name = 'risk_management'

urlpatterns = [
    # Dashboard GRO
    path('', views.gro_dashboard, name='dashboard'),

    # Perigos (CRUD)
    path('hazards/', views.hazard_list, name='hazard_list'),
    path('hazards/create/', views.hazard_create, name='hazard_create'),
    path('hazards/<int:pk>/edit/', views.hazard_edit, name='hazard_edit'),
    path('hazards/<int:pk>/delete/', views.hazard_delete, name='hazard_delete'),

    # Aprovação/Rejeição de perigos auto-gerados
    path('hazards/<int:pk>/approve/', views.approve_hazard, name='approve_hazard'),
    path('hazards/<int:pk>/reject/', views.reject_hazard, name='reject_hazard'),
    path('hazards/approve-all/', views.approve_all_hazards, name='approve_all_hazards'),

    # Geração automática de perigos a partir de pesquisa
    path('hazards/generate/<int:form_pk>/', views.generate_hazards_from_survey, name='generate_hazards'),

    # Avaliação de Risco
    path('hazards/<int:hazard_pk>/assess/', views.risk_assess, name='risk_assess'),
    path('matrix/', views.risk_matrix_view, name='risk_matrix'),

    # Medidas de Controle
    path('assessment/<int:assessment_pk>/controls/', views.control_measures, name='control_measures'),
    path('control/<int:pk>/toggle/', views.toggle_control, name='toggle_control'),

    # Planos de Ação
    path('action-plans/', views.action_plan_list, name='action_plan_list'),
    path('action-plans/create/', views.action_plan_create, name='action_plan_create'),
    path('action-plans/<int:pk>/edit/', views.action_plan_edit, name='action_plan_edit'),
    path('action-plans/<int:pk>/status/', views.action_plan_status, name='action_plan_status'),

    # Comparação de Pesquisas (Evolução)
    path('compare/', views.compare_surveys_view, name='compare_surveys'),
]

