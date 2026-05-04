"""URLs para Alertas Inteligentes."""
from django.urls import path
from . import views

app_name = 'alerts'

urlpatterns = [
    path('', views.alert_list, name='list'),
    path('<int:pk>/read/', views.mark_read, name='mark_read'),
    path('<int:pk>/resolve/', views.mark_resolved, name='mark_resolved'),
    path('mark-all-read/', views.mark_all_read, name='mark_all_read'),
    path('api/count/', views.unread_count_api, name='unread_count'),
    path('run-checks/', views.run_checks_manual, name='run_checks'),
]
