"""
URLs para gestao de formularios.
"""
from django.urls import path
from . import views

app_name = 'forms'

urlpatterns = [
    path('templates/', views.template_list, name='templates'),
    path('templates/<int:pk>/', views.template_detail, name='template_detail'),
    
    path('', views.form_instance_list, name='instances'),
    path('create/<int:template_pk>/', views.form_instance_create, name='instance_create'),
    path('<int:pk>/', views.form_instance_detail, name='instance_detail'),
    path('<int:pk>/publish/', views.form_instance_publish, name='instance_publish'),
    path('<int:pk>/resync/', views.form_instance_resync, name='instance_resync'),
    path('<int:pk>/close/', views.form_instance_close, name='instance_close'),
    
    path('respond/<int:assignment_pk>/', views.form_respond, name='respond'),
    path('responses/<int:assignment_pk>/', views.form_view_responses, name='view_responses'),
    path('resend-notification/<int:assignment_pk>/', views.resend_form_notification, name='resend_notification'),
]
