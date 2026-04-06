"""
URLs para gestao de empresas.
"""
from django.urls import path
from . import views

app_name = 'companies'

urlpatterns = [
    path('', views.company_list, name='list'),
    path('<int:pk>/approve/', views.company_approve, name='approve'),
    path('<int:pk>/reject/', views.company_reject, name='reject'),
    path('<int:pk>/edit/', views.company_edit, name='edit'),
    path('<int:pk>/delete/', views.company_delete, name='delete'),
    path('<int:pk>/suspend/', views.company_suspend, name='suspend'),
    path('settings/', views.company_settings, name='settings'),
    
    path('announcements/', views.announcement_list, name='announcements'),
    path('announcements/create/', views.announcement_create, name='announcement_create'),
    path('announcements/<int:pk>/toggle/', views.announcement_toggle, name='announcement_toggle'),
]
