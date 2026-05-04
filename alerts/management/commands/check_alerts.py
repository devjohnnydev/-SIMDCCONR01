"""
Management command para executar verificações de alertas manualmente.
Uso: python manage.py check_alerts
Alternativa ao Celery para ambientes sem Redis.
"""
from django.core.management.base import BaseCommand
from alerts.services import run_all_checks


class Command(BaseCommand):
    help = 'Executa todas as verificações de alertas (laudos expirando, riscos altos, prazos vencidos)'

    def handle(self, *args, **options):
        self.stdout.write('Iniciando verificação de alertas...')
        results = run_all_checks()
        self.stdout.write(
            self.style.SUCCESS(
                f'Verificação concluída! {results["total_created"]} alertas criados.'
            )
        )
        for check, count in results['details'].items():
            self.stdout.write(f'  - {check}: {count} alertas')
