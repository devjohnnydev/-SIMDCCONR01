"""
URLs para gestao de funcionarios.
"""
from django.urls import path
from . import views

app_name = 'employees'

urlpatterns = [
    path('', views.employee_list, name='list'),
    path('create/', views.employee_create, name='create'),
    path('<int:pk>/edit/', views.employee_edit, name='edit'),
    path('<int:pk>/deactivate/', views.employee_deactivate, name='deactivate'),
    path('<int:pk>/create-user/', views.employee_create_user, name='create_user'),
    
    path('import/', views.employee_import, name='import'),
    path('export-template/', views.employee_export_template, name='export_template'),
]
