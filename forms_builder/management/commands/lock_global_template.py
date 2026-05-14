"""Comando para travar o template global SIMDCCONR01 como imutável."""
from django.core.management.base import BaseCommand
from forms_builder.models import FormTemplate


class Command(BaseCommand):
    help = 'Trava o template global SIMDCCONR01 (is_locked=True)'

    def handle(self, *args, **options):
        updated = FormTemplate.objects.filter(
            is_global=True
        ).update(is_locked=True)

        self.stdout.write(
            self.style.SUCCESS(f'{updated} template(s) global(is) travado(s) com sucesso.')
        )
