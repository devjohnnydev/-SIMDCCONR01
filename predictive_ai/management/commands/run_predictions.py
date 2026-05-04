"""Management command para executar análise preditiva."""
from django.core.management.base import BaseCommand
from predictive_ai.services import run_predictive_analysis


class Command(BaseCommand):
    help = 'Executa análise preditiva de tendências para todas as empresas.'

    def handle(self, *args, **options):
        self.stdout.write('Iniciando análise preditiva...')
        results = run_predictive_analysis()
        self.stdout.write(self.style.SUCCESS(
            f'Análise concluída! '
            f'{results["companies_analyzed"]} empresas analisadas, '
            f'{results["alerts_created"]} alertas gerados.'
        ))
