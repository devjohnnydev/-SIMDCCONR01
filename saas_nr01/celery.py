"""
Configuração do Celery para o projeto SIMDCCONR01.
"""
import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'saas_nr01.settings')

app = Celery('saas_nr01')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Beat schedule — tarefas periódicas
app.conf.beat_schedule = {
    'check-alerts-daily': {
        'task': 'alerts.tasks.run_daily_checks',
        'schedule': crontab(hour=8, minute=0),  # Todo dia às 8h
        'options': {'queue': 'default'},
    },
    'check-alerts-urgent': {
        'task': 'alerts.tasks.run_daily_checks',
        'schedule': crontab(hour=14, minute=0),  # Verificação extra às 14h
        'options': {'queue': 'default'},
    },
    'send-alert-emails': {
        'task': 'alerts.tasks.send_alert_emails',
        'schedule': crontab(hour=9, minute=0),  # Emails diários às 9h
        'options': {'queue': 'default'},
    },
    'run-predictive-analysis-weekly': {
        'task': 'alerts.tasks.run_predictive_analysis',
        'schedule': crontab(hour=7, minute=0, day_of_week=1),  # Toda segunda às 7h
        'options': {'queue': 'default'},
    },
}
