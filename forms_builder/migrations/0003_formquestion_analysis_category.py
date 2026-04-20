from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('forms_builder', '0002_category_update'),
    ]

    operations = [
        migrations.AddField(
            model_name='formquestion',
            name='analysis_category',
            field=models.CharField(
                choices=[
                    ('DIAGNOSTICO', 'Diagnóstico Psicossocial'),
                    ('DISSONANCIA', 'Dissonância de Clima e Cultura'),
                    ('RISCOS', 'Riscos Identificados (PGR/GRO)'),
                    ('RECOMENDACOES', 'Recomendações de Ação'),
                ],
                default='DIAGNOSTICO',
                help_text='Define em qual seção do laudo esta pergunta será agrupada',
                max_length=20,
                verbose_name='Categoria de Análise',
            ),
        ),
    ]
