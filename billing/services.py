"""
Serviço de métricas financeiras para o Dashboard Executivo.
Cálculos de MRR, ticket médio, inadimplência e previsão de faturamento.
"""
from decimal import Decimal
from django.utils import timezone
from django.db.models import Sum, Count, Avg, Q
from datetime import timedelta


def calculate_financial_metrics():
    """
    Calcula métricas financeiras consolidadas para o Admin Master.
    Returns: dict com todas as métricas.
    """
    from .models import Subscription, PaymentOrder
    from companies.models import Company

    now = timezone.now()

    # Assinaturas ativas
    active_subs = Subscription.objects.filter(status='ACTIVE')
    total_active = active_subs.count()

    # MRR (Monthly Recurring Revenue) — normaliza semestral e anual para mensal
    mrr = Decimal('0.00')
    for sub in active_subs:
        price = sub.calculated_price or sub.plan.price_monthly
        if sub.billing_cycle == 'SEMESTRAL':
            mrr += price / 6
        elif sub.billing_cycle == 'YEARLY' or sub.is_yearly:
            mrr += price / 12
        else:
            mrr += price
    mrr = round(mrr, 2)

    # ARR (Annual Recurring Revenue)
    arr = round(mrr * 12, 2)

    # Ticket Médio
    ticket_medio = round(mrr / total_active, 2) if total_active > 0 else Decimal('0.00')

    # Receita por empresa (top 10)
    revenue_by_company = []
    for sub in active_subs.select_related('company', 'plan')[:10]:
        price = sub.calculated_price or sub.plan.price_monthly
        revenue_by_company.append({
            'company_name': sub.company.nome_fantasia,
            'plan_name': sub.plan.name,
            'monthly_value': round(price / 6, 2) if sub.billing_cycle == 'SEMESTRAL' else price,
            'total_value': price,
            'cycle': sub.get_billing_cycle_display(),
            'employees': sub.employee_count_at_subscription,
        })

    # Inadimplência — pagamentos vencidos e não pagos
    overdue_threshold = now - timedelta(days=30)
    overdue_payments = PaymentOrder.objects.filter(
        status__in=['PENDING', 'FAILED'],
        created_at__lte=overdue_threshold
    )
    total_inadimplencia = overdue_payments.aggregate(
        total=Sum('amount')
    )['total'] or 0
    # amount é em centavos, converter para reais
    total_inadimplencia = Decimal(total_inadimplencia) / 100
    inadimplencia_count = overdue_payments.count()

    # Previsão de faturamento semestral
    previsao_semestral = round(mrr * 6, 2)

    # Pagamentos recentes (últimos 30 dias)
    recent_paid = PaymentOrder.objects.filter(
        status='PAID',
        paid_at__gte=now - timedelta(days=30)
    )
    receita_30d = recent_paid.aggregate(
        total=Sum('amount')
    )['total'] or 0
    receita_30d = Decimal(receita_30d) / 100

    # Crescimento: novas assinaturas últimos 30 dias
    new_subs_30d = Subscription.objects.filter(
        start_date__gte=(now - timedelta(days=30)).date()
    ).count()

    # Churn: cancelamentos últimos 30 dias
    churn_30d = Subscription.objects.filter(
        status='CANCELLED',
        end_date__gte=(now - timedelta(days=30)).date()
    ).count()

    # Empresas ativas sem assinatura (potencial de conversão)
    companies_sem_plano = Company.objects.filter(
        status='ACTIVE',
        plan__isnull=True
    ).count()

    return {
        'total_active_subs': total_active,
        'mrr': mrr,
        'arr': arr,
        'ticket_medio': ticket_medio,
        'revenue_by_company': revenue_by_company,
        'total_inadimplencia': total_inadimplencia,
        'inadimplencia_count': inadimplencia_count,
        'previsao_semestral': previsao_semestral,
        'receita_30d': receita_30d,
        'new_subs_30d': new_subs_30d,
        'churn_30d': churn_30d,
        'companies_sem_plano': companies_sem_plano,
    }
