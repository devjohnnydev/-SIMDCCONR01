"""
Serviço de geração automática de alertas.
Executado periodicamente via Celery beat ou management command.
"""
from django.utils import timezone
from datetime import timedelta

from .models import Alert


def check_expiring_reports(days_ahead=30):
    """Verifica laudos/documentos com validade próxima de expirar."""
    from documents.models import Document

    threshold = timezone.now().date() + timedelta(days=days_ahead)
    expiring = Document.objects.filter(
        status='ACTIVE',
        validade__isnull=False,
        validade__lte=threshold,
        validade__gt=timezone.now().date()
    )

    created = 0
    for doc in expiring:
        days_left = (doc.validade - timezone.now().date()).days
        existing = Alert.objects.filter(
            company=doc.company,
            tipo='REPORT_EXPIRING',
            related_object_type='documents.Document',
            related_object_id=doc.id,
            is_resolved=False
        ).exists()

        if not existing:
            Alert.objects.create(
                company=doc.company,
                tipo='REPORT_EXPIRING',
                severidade='WARNING' if days_left > 7 else 'CRITICAL',
                titulo=f'Documento expirando em {days_left} dias',
                mensagem=f'O documento "{doc.titulo}" (v{doc.versao}) '
                         f'expira em {doc.validade.strftime("%d/%m/%Y")}. '
                         f'Providencie a atualização.',
                related_object_type='documents.Document',
                related_object_id=doc.id,
            )
            created += 1
    return created


def check_high_risks():
    """Verifica riscos com nível substancial ou intolerável sem ação."""
    from risk_management.models import RiskAssessment

    high_risks = RiskAssessment.objects.filter(
        nivel_risco__in=['SUBSTANCIAL', 'INTOLERAVEL'],
        hazard__status='ACTIVE'
    ).select_related('hazard', 'hazard__company')

    created = 0
    for assessment in high_risks:
        has_action = assessment.action_plans.filter(
            status__in=['PENDENTE', 'EM_ANDAMENTO']
        ).exists()

        if not has_action:
            existing = Alert.objects.filter(
                company=assessment.hazard.company,
                tipo='RISK_CRITICAL',
                related_object_type='risk_management.RiskAssessment',
                related_object_id=assessment.id,
                is_resolved=False
            ).exists()

            if not existing:
                Alert.objects.create(
                    company=assessment.hazard.company,
                    tipo='RISK_CRITICAL',
                    severidade='CRITICAL',
                    titulo=f'Risco {assessment.nivel_risco} sem plano de ação',
                    mensagem=f'O perigo "{assessment.hazard.descricao_perigo[:80]}" '
                             f'no setor {assessment.hazard.setor} foi avaliado como '
                             f'{assessment.get_nivel_risco_display()} e não possui '
                             f'plano de ação ativo.',
                    related_object_type='risk_management.RiskAssessment',
                    related_object_id=assessment.id,
                )
                created += 1
    return created


def check_overdue_action_plans():
    """Verifica planos de ação com prazo vencido."""
    from risk_management.models import ActionPlan

    overdue = ActionPlan.objects.filter(
        status__in=['PENDENTE', 'EM_ANDAMENTO'],
        prazo_fim__lt=timezone.now().date()
    )

    created = 0
    for plan in overdue:
        days_overdue = (timezone.now().date() - plan.prazo_fim).days
        existing = Alert.objects.filter(
            company=plan.company,
            tipo='DEADLINE_OVERDUE',
            related_object_type='risk_management.ActionPlan',
            related_object_id=plan.id,
            is_resolved=False
        ).exists()

        if not existing:
            Alert.objects.create(
                company=plan.company,
                tipo='DEADLINE_OVERDUE',
                severidade='CRITICAL',
                titulo=f'Plano de ação vencido há {days_overdue} dias',
                mensagem=f'A ação "{plan.titulo[:80]}" deveria ter sido concluída '
                         f'em {plan.prazo_fim.strftime("%d/%m/%Y")}. '
                         f'Responsável: {plan.responsavel}.',
                related_object_type='risk_management.ActionPlan',
                related_object_id=plan.id,
            )
            created += 1
    return created


def check_health_score_decline():
    """Verifica se o score de risco de alguma empresa piorou."""
    from evolution.models import RiskScoreHistory
    from companies.models import Company

    companies = Company.objects.filter(status='ACTIVE')
    created = 0

    for company in companies:
        scores = RiskScoreHistory.objects.filter(
            company=company
        ).order_by('-date')[:2]

        if scores.count() >= 2:
            current = scores[0]
            previous = scores[1]
            diff = current.score - previous.score

            if diff >= 10:  # Piora significativa (10+ pontos)
                existing = Alert.objects.filter(
                    company=company,
                    tipo='SCORE_DECLINE',
                    is_resolved=False,
                    created_at__gte=timezone.now() - timedelta(days=30)
                ).exists()

                if not existing:
                    Alert.objects.create(
                        company=company,
                        tipo='SCORE_DECLINE',
                        severidade='WARNING' if diff < 20 else 'CRITICAL',
                        titulo=f'Score de risco piorou: {previous.score} → {current.score}',
                        mensagem=f'O score de risco da empresa subiu {diff} pontos. '
                                 f'Faixa atual: {current.get_faixa_display()}. '
                                 f'Avalie as dimensões que contribuíram para a piora.',
                    )
                    created += 1
    return created


def check_approaching_deadlines(days_ahead=7):
    """Verifica planos de ação com prazo próximo."""
    from risk_management.models import ActionPlan

    threshold = timezone.now().date() + timedelta(days=days_ahead)
    approaching = ActionPlan.objects.filter(
        status__in=['PENDENTE', 'EM_ANDAMENTO'],
        prazo_fim__lte=threshold,
        prazo_fim__gt=timezone.now().date()
    )

    created = 0
    for plan in approaching:
        days_left = (plan.prazo_fim - timezone.now().date()).days
        existing = Alert.objects.filter(
            company=plan.company,
            tipo='DEADLINE_APPROACHING',
            related_object_type='risk_management.ActionPlan',
            related_object_id=plan.id,
            is_resolved=False
        ).exists()

        if not existing:
            Alert.objects.create(
                company=plan.company,
                tipo='DEADLINE_APPROACHING',
                severidade='WARNING',
                titulo=f'Prazo vencendo em {days_left} dias',
                mensagem=f'A ação "{plan.titulo[:80]}" vence em '
                         f'{plan.prazo_fim.strftime("%d/%m/%Y")}. '
                         f'Responsável: {plan.responsavel}.',
                related_object_type='risk_management.ActionPlan',
                related_object_id=plan.id,
            )
            created += 1
    return created


def run_all_checks():
    """Executa todas as verificações de alertas. Chamado pelo Celery."""
    results = {
        'expiring_reports': check_expiring_reports(),
        'high_risks': check_high_risks(),
        'overdue_plans': check_overdue_action_plans(),
        'health_decline': check_health_score_decline(),
        'approaching_deadlines': check_approaching_deadlines(),
    }
    total = sum(results.values())
    return {'total_created': total, 'details': results}
