"""
Migration para criar o modelo SignerProfile e adicionar FK ao EmployeeDiagnostic.
"""

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0005_employeediagnostic_assigned_professional_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='SignerProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome_completo', models.CharField(max_length=200, verbose_name='Nome Completo')),
                ('registro_profissional', models.CharField(blank=True, max_length=50, verbose_name='Registro Profissional (CRP/CRM/CREA)')),
                ('especialidade', models.CharField(
                    choices=[
                        ('PSICOLOGO', 'Psicólogo(a)'),
                        ('MEDICO_TRABALHO', 'Médico(a) do Trabalho'),
                        ('ENGENHEIRO_SEG', 'Engenheiro(a) de Segurança'),
                        ('TECNICO_SEG', 'Técnico(a) em Segurança'),
                        ('ADMINISTRADOR', 'Administrador(a)'),
                        ('OUTRO', 'Outro'),
                    ],
                    default='PSICOLOGO',
                    max_length=30,
                    verbose_name='Especialidade'
                )),
                ('email', models.EmailField(blank=True, verbose_name='E-mail de Contato')),
                ('govbr_cpf', models.CharField(blank=True, max_length=11, verbose_name='CPF (Gov.br)')),
                ('signature_image', models.ImageField(
                    blank=True,
                    null=True,
                    upload_to='signatures/professionals/',
                    verbose_name='Imagem da Assinatura'
                )),
                ('is_active', models.BooleanField(default=True, verbose_name='Ativo')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Cadastrado em')),
            ],
            options={
                'verbose_name': 'Perfil de Signatário',
                'verbose_name_plural': 'Perfis de Signatários',
                'ordering': ['nome_completo'],
            },
        ),
        migrations.AddField(
            model_name='employeediagnostic',
            name='signer_profile',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='signed_diagnostics',
                to='reports.signerprofile',
                verbose_name='Perfil do Signatário'
            ),
        ),
    ]
