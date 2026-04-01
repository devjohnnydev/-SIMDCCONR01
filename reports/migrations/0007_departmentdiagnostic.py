"""
Migration for DepartmentDiagnostic model.
"""

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0006_signerprofile_and_diagnostic_fk'),
        ('companies', '0001_initial'),
        ('forms_builder', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='DepartmentDiagnostic',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('setor', models.CharField(max_length=100, verbose_name='Setor/Departamento')),
                ('diagnostic_data', models.JSONField(default=dict, verbose_name='Dados da Análise (IA)')),
                ('generated_at', models.DateTimeField(auto_now_add=True, verbose_name='Gerado em')),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='department_diagnostics', to='companies.company', verbose_name='Empresa')),
                ('form_instance', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='department_diagnostics', to='forms_builder.forminstance', verbose_name='Formulário')),
                ('generated_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='department_diagnostics', to='accounts.user', verbose_name='Gerado por')),
            ],
            options={
                'verbose_name': 'Laudo de Departamento',
                'verbose_name_plural': 'Laudos de Departamento',
                'ordering': ['-generated_at'],
                'unique_together': {('company', 'setor', 'form_instance')},
            },
        ),
    ]
