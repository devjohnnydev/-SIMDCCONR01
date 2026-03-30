"""
URLs para billing e planos.
"""
from django.urls import path
from . import views

app_name = 'billing'

urlpatterns = [
    path('plan/', views.plan_current, name='current_plan'),
    path('plans/', views.plan_list, name='plan_list'),
    path('pricing/', views.plan_pricing, name='pricing'),
]
