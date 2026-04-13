"""
Views para billing: pricing, checkout Stripe e webhooks.
"""
import logging
import stripe

from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils import timezone
from datetime import timedelta

from .models import Plan, Subscription, PaymentOrder
from companies.views import require_company_admin, require_admin_master

logger = logging.getLogger(__name__)

# Configura API key do Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


def _activate_plan_for_company(company, plan, is_yearly=False, payment_intent_id=''):
    """Logica centralizada para ativar um plano para uma empresa."""
    company.plan = plan
    company.subscription_status = 'active'

    now = timezone.now()
    if is_yearly:
        company.current_period_end = now + timedelta(days=365)
    else:
        company.current_period_end = now + timedelta(days=30)

    # IMPORTANTE: nao incluir 'updated_at' pois é auto_now=True
    company.save(update_fields=[
        'plan', 'subscription_status', 'current_period_end'
    ])

    # Cria registro de Subscription (se nao existir para este periodo)
    Subscription.objects.get_or_create(
        company=company,
        plan=plan,
        status='ACTIVE',
        defaults={
            'start_date': now.date(),
            'end_date': company.current_period_end.date(),
            'is_yearly': is_yearly,
        }
    )

    logger.info(
        f'Empresa {company.nome_fantasia} (ID:{company.id}) '
        f'ativou plano {plan.name} (yearly={is_yearly})'
    )


@login_required
def plan_pricing(request):
    """Pagina de precos e planos — acessivel por COMPANY_ADMIN (com ou sem plano)."""
    plans = Plan.objects.filter(is_active=True).order_by('order')[:3]

    current_plan = None
    company = None
    usage = {}
    limits = None

    if hasattr(request.user, 'company') and request.user.company:
        company = request.user.company
        current_plan = company.plan

        if current_plan:
            usage = {
                'employees': company.get_employee_count(),
                'forms': company.get_active_forms_count(),
            }
            limits = {
                'max_employees': current_plan.max_employees,
                'max_forms': current_plan.max_forms,
                'employees_percent': round(
                    (usage['employees'] / current_plan.max_employees) * 100, 1
                ) if current_plan.max_employees > 0 else 0,
                'forms_percent': round(
                    (usage['forms'] / current_plan.max_forms) * 100, 1
                ) if current_plan.max_forms > 0 else 0,
            }

    context = {
        'plans': plans,
        'current_plan': current_plan,
        'company': company,
        'usage': usage,
        'limits': limits,
        'stripe_public_key': settings.STRIPE_PUBLIC_KEY,
        'has_no_plan': company and not current_plan,
    }

    return render(request, 'billing/pricing.html', context)


@login_required
@require_company_admin
@require_POST
def create_checkout_session(request):
    """Cria sessao de checkout do Stripe e redireciona o usuario."""
    company = request.user.company
    plan_id = request.POST.get('plan_id')
    is_yearly = request.POST.get('billing_cycle') == 'yearly'

    plan = get_object_or_404(Plan, pk=plan_id, is_active=True)

    # Calcula valor em centavos
    if is_yearly and plan.price_yearly:
        amount = int(plan.price_yearly * 100)
        period_label = 'Anual'
    else:
        amount = int(plan.price_monthly * 100)
        period_label = 'Mensal'
        is_yearly = False

    # Cria order local com status pending
    order = PaymentOrder.objects.create(
        company=company,
        plan=plan,
        is_yearly=is_yearly,
        amount=amount,
        status='pending',
    )

    try:
        # Cria sessao no Stripe Checkout
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card', 'boleto'],
            mode='payment',
            line_items=[{
                'price_data': {
                    'currency': 'brl',
                    'product_data': {
                        'name': f'Plano {plan.name} — {period_label}',
                        'description': plan.description[:500] if plan.description else f'Assinatura {period_label} do plano {plan.name}',
                    },
                    'unit_amount': amount,
                },
                'quantity': 1,
            }],
            metadata={
                'company_id': str(company.id),
                'order_id': str(order.id),
                'plan_id': str(plan.id),
                'is_yearly': '1' if is_yearly else '0',
            },
            customer_email=company.responsavel_email,
            success_url=f'{settings.SITE_URL}/billing/success/?session_id={{CHECKOUT_SESSION_ID}}',
            cancel_url=f'{settings.SITE_URL}/billing/cancel/',
        )

        # Salva session_id na order para idempotencia
        order.stripe_session_id = checkout_session.id
        order.save(update_fields=['stripe_session_id'])

        logger.info(f'Checkout session criada: {checkout_session.id} para empresa {company.id}')

        return redirect(checkout_session.url)

    except stripe.error.StripeError as e:
        logger.error(f'Stripe error ao criar checkout: {e}')
        order.status = 'failed'
        order.save(update_fields=['status'])
        messages.error(request, f'Erro ao processar pagamento: {str(e)}')
        return redirect('billing:pricing')
    except Exception as e:
        logger.error(f'Erro inesperado ao criar checkout: {e}')
        order.status = 'failed'
        order.save(update_fields=['status'])
        messages.error(request, 'Ocorreu um erro inesperado. Tente novamente.')
        return redirect('billing:pricing')


@csrf_exempt
@require_POST
def stripe_webhook(request):
    """Webhook do Stripe — valida assinatura e processa eventos de pagamento."""
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')
    webhook_secret = settings.STRIPE_WEBHOOK_SECRET

    if not webhook_secret:
        logger.error('STRIPE_WEBHOOK_SECRET nao configurado')
        return HttpResponse('Webhook secret not configured', status=500)

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except ValueError:
        logger.error('Webhook: payload invalido')
        return HttpResponse('Invalid payload', status=400)
    except stripe.error.SignatureVerificationError:
        logger.error('Webhook: assinatura invalida')
        return HttpResponse('Invalid signature', status=400)

    event_type = event['type']
    logger.info(f'Webhook recebido: {event_type} (id: {event["id"]})')

    # --- checkout.session.completed ---
    if event_type == 'checkout.session.completed':
        session = event['data']['object']
        _handle_checkout_completed(session)

    # --- payment_intent.succeeded ---
    elif event_type == 'payment_intent.succeeded':
        intent = event['data']['object']
        logger.info(f'PaymentIntent succeeded: {intent["id"]}')

    # --- payment_intent.payment_failed ---
    elif event_type == 'payment_intent.payment_failed':
        intent = event['data']['object']
        logger.warning(f'PaymentIntent FALHOU: {intent["id"]}')
        PaymentOrder.objects.filter(
            stripe_payment_intent_id=intent['id'],
            status='pending'
        ).update(status='failed')

    else:
        logger.info(f'Webhook evento nao tratado: {event_type}')

    return HttpResponse('OK', status=200)


def _handle_checkout_completed(session):
    """Processa checkout.session.completed — ativa plano da empresa."""
    metadata = session.get('metadata', {})

    company_id = metadata.get('company_id')
    order_id = metadata.get('order_id')
    plan_id = metadata.get('plan_id')
    is_yearly = metadata.get('is_yearly') == '1'

    if not all([company_id, order_id, plan_id]):
        logger.error(f'Checkout completed com metadata incompleta: {metadata}')
        return

    # Idempotencia: verifica se ja foi processado
    try:
        order = PaymentOrder.objects.get(id=order_id)
    except PaymentOrder.DoesNotExist:
        logger.error(f'PaymentOrder {order_id} nao encontrada')
        return

    if order.status == 'paid':
        logger.info(f'Order {order_id} ja processada (idempotencia). Ignorando.')
        return

    # Marca como pago
    order.status = 'paid'
    order.paid_at = timezone.now()
    order.stripe_payment_intent_id = session.get('payment_intent', '')
    order.save(update_fields=['status', 'paid_at', 'stripe_payment_intent_id'])

    # Atribui plano a empresa
    try:
        from companies.models import Company
        company = Company.objects.get(id=company_id)
        plan = Plan.objects.get(id=plan_id)
        _activate_plan_for_company(company, plan, is_yearly, session.get('payment_intent', ''))
    except Exception as e:
        logger.error(f'Erro ao ativar plano via webhook: {e}', exc_info=True)


@login_required
def checkout_success(request):
    """Pagina de sucesso apos pagamento — com fallback de ativacao."""
    session_id = request.GET.get('session_id', '')
    company = getattr(request.user, 'company', None)

    order = None
    plan = None

    if session_id and company:
        # Buscar order local
        order = PaymentOrder.objects.filter(
            stripe_session_id=session_id,
            company=company
        ).first()

        # FALLBACK: se o webhook nao processou, verifica com a API do Stripe
        if order and order.status == 'pending':
            try:
                stripe_session = stripe.checkout.Session.retrieve(session_id)
                if stripe_session.payment_status == 'paid':
                    # Marca order como paga
                    order.status = 'paid'
                    order.paid_at = timezone.now()
                    order.stripe_payment_intent_id = stripe_session.payment_intent or ''
                    order.save(update_fields=['status', 'paid_at', 'stripe_payment_intent_id'])

                    # Ativa plano se ainda nao ativo
                    if not company.has_active_plan or company.plan_id != order.plan_id:
                        _activate_plan_for_company(
                            company, order.plan,
                            order.is_yearly,
                            stripe_session.payment_intent or ''
                        )
                        # Recarrega company do banco
                        company.refresh_from_db()

                    logger.info(f'Plano ativado via fallback success page para empresa {company.id}')

            except stripe.error.StripeError as e:
                logger.error(f'Erro ao verificar sessao Stripe no fallback: {e}')
            except Exception as e:
                logger.error(f'Erro inesperado no fallback success: {e}', exc_info=True)

        if order:
            plan = order.plan

    context = {
        'order': order,
        'plan': plan,
    }
    return render(request, 'billing/checkout_success.html', context)


@login_required
def checkout_cancel(request):
    """Pagina exibida quando o usuario cancela o checkout."""
    return render(request, 'billing/checkout_cancel.html')


@login_required
@require_admin_master
def plan_list(request):
    """Lista todos os planos (ADMIN_MASTER)."""
    plans = Plan.objects.all().order_by('order')
    orders = PaymentOrder.objects.select_related('company', 'plan').order_by('-created_at')[:50]
    return render(request, 'billing/plan_list.html', {
        'plans': plans,
        'orders': orders,
    })
