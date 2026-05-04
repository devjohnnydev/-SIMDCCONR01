"""Management command para popular o banco de sugestões NR."""
from django.core.management.base import BaseCommand
from predictive_ai.services import seed_nr_suggestions


class Command(BaseCommand):
    help = 'Popula o banco de sugestões NR com recomendações padrão.'

    def handle(self, *args, **options):
        created = seed_nr_suggestions()
        self.stdout.write(self.style.SUCCESS(
            f'{created} sugestões NR criadas com sucesso.'
        ))
