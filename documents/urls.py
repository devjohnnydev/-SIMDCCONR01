"""URLs para Gestão de Documentos."""
from django.urls import path
from . import views

app_name = 'documents'

urlpatterns = [
    path('', views.document_list, name='list'),
    path('upload/', views.document_upload, name='upload'),
    path('<int:pk>/', views.document_detail, name='detail'),
    path('<int:pk>/new-version/', views.document_new_version, name='new_version'),
    path('<int:pk>/download/', views.document_download, name='download'),
]
