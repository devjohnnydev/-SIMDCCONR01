"""
URLs para billing, checkout Stripe e webhooks.
"""
from django.urls import path
from . import views

app_name = 'billing'

urlpatterns = [
    # Pagina principal de planos/precos
    path('pricing/', views.plan_pricing, name='pricing'),
    path('plan/', views.plan_pricing, name='current_plan'),

    # Custom Plans Flow
    path('pricing/custom-request/', views.request_custom_plan, name='request_custom_plan'),
    path('pricing/custom-request/<int:request_id>/checkout/', views.checkout_custom_plan, name='checkout_custom_plan'),
    path('pricing/custom-request/<int:request_id>/cancel/', views.cancel_custom_plan, name='cancel_custom_plan'),

    # Checkout Stripe
    path('checkout/', views.create_checkout_session, name='create_checkout'),
    path('success/', views.checkout_success, name='checkout_success'),
    path('cancel/', views.checkout_cancel, name='checkout_cancel'),

    # Webhook Stripe (csrf_exempt aplicado na view)
    path('webhook/stripe/', views.stripe_webhook, name='stripe_webhook'),

    # Admin Master — listagem de planos e orders
    path('plans/', views.plan_list, name='plan_list'),
    
    # Admin Master — Custom Plans
    path('admin/custom-requests/', views.admin_custom_requests, name='admin_custom_requests'),
    path('admin/custom-requests/<int:request_id>/', views.admin_custom_request_detail, name='admin_custom_request_detail'),
]
