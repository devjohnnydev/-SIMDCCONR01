"""
Celery tasks para alertas automáticos.
"""
from celery import shared_task
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)


@shared_task(name='alerts.tasks.run_daily_checks')
def run_daily_checks():
    """
    Task executada diariamente pelo Celery Beat.
    Verifica: laudos expirando, riscos altos, planos vencidos, score em queda.
    """
    from .services import run_all_checks

    logger.info('Iniciando verificação diária de alertas...')
    results = run_all_checks()
    logger.info(f'Verificação concluída: {results["total_created"]} alertas criados.')
    logger.info(f'Detalhes: {results["details"]}')
    return results


@shared_task(name='alerts.tasks.send_alert_emails')
def send_alert_emails():
    """
    Envia emails de alertas críticos não enviados.
    """
    from django.core.mail import send_mail
    from django.conf import settings
    from .models import Alert

    unsent = Alert.objects.filter(
        is_email_sent=False,
        severidade='CRITICAL'
    ).select_related('company', 'target_user')[:50]

    sent = 0
    for alert in unsent:
        recipients = []
        if alert.target_user and alert.target_user.email:
            recipients.append(alert.target_user.email)
        else:
            # Enviar para admins da empresa
            from accounts.models import User
            admins = User.objects.filter(
                company=alert.company,
                role='COMPANY_ADMIN',
                is_active=True
            ).values_list('email', flat=True)
            recipients = list(admins)

        if recipients:
            try:
                send_mail(
                    subject=f'[SIMDCCONR01] {alert.get_severidade_display()}: {alert.titulo}',
                    message=f'{alert.mensagem}\n\nEmpresa: {alert.company.nome_fantasia}\n'
                            f'Tipo: {alert.get_tipo_display()}\n'
                            f'Data: {alert.created_at.strftime("%d/%m/%Y %H:%M")}',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=recipients,
                    fail_silently=True,
                )
                alert.is_email_sent = True
                alert.save(update_fields=['is_email_sent'])
                sent += 1
            except Exception as e:
                logger.error(f'Erro ao enviar email de alerta {alert.pk}: {e}')

    logger.info(f'{sent} emails de alertas enviados.')
    return {'sent': sent}


@shared_task(name='alerts.tasks.run_predictive_analysis')
def run_predictive_analysis_task():
    """
    Task executada semanalmente pelo Celery Beat.
    Analisa tendências de setores, riscos crescentes e dimensões em queda.
    """
    from predictive_ai.services import run_predictive_analysis

    logger.info('Iniciando análise preditiva de IA...')
    results = run_predictive_analysis()
    logger.info(
        f'Análise preditiva concluída: {results["companies_analyzed"]} empresas, '
        f'{results["alerts_created"]} alertas gerados.'
    )
    return results
