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

    # Checkout Stripe
    path('checkout/', views.create_checkout_session, name='create_checkout'),
    path('success/', views.checkout_success, name='checkout_success'),
    path('cancel/', views.checkout_cancel, name='checkout_cancel'),

    # Webhook Stripe (csrf_exempt aplicado na view)
    path('webhook/stripe/', views.stripe_webhook, name='stripe_webhook'),

    # Admin Master — listagem de planos e orders
    path('plans/', views.plan_list, name='plan_list'),
]
