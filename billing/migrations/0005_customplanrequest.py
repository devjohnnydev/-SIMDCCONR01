# Generated manually

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('companies', '0001_initial'), # or whatever companies dependency is
        ('billing', '0004_rename_billing_pay_stripe__idx_billing_pay_stripe__6870d9_idx'),
    ]

    operations = [
        migrations.CreateModel(
            name='CustomPlanRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('pending', 'Pendente de Análise'), ('proposed', 'Proposta Enviada'), ('accepted', 'Aceita / Assinada'), ('rejected', 'Recusada / Cancelada')], default='pending', max_length=20, verbose_name='Status')),
                ('max_employees', models.IntegerField(default=50, verbose_name='Limite de Funcionários')),
                ('max_forms', models.IntegerField(default=10, verbose_name='Limite de Formulários Ativos')),
                ('max_reports', models.IntegerField(default=20, verbose_name='Relatórios por Mês')),
                ('data_retention_days', models.IntegerField(default=365, verbose_name='Retenção de Dados (dias)')),
                ('has_pdf_export', models.BooleanField(default=True, verbose_name='Exportação PDF')),
                ('has_csv_import', models.BooleanField(default=True, verbose_name='Importação CSV')),
                ('has_api_access', models.BooleanField(default=False, verbose_name='Acesso API')),
                ('has_custom_branding', models.BooleanField(default=True, verbose_name='Personalização Visual')),
                ('has_priority_support', models.BooleanField(default=False, verbose_name='Suporte Prioritário')),
                ('proposed_price_monthly', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Preço Mensal Proposto')),
                ('proposed_price_yearly', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Preço Anual Proposto')),
                ('admin_message', models.TextField(blank=True, verbose_name='Mensagem do Admin')),
                ('user_message', models.TextField(blank=True, help_text='Usado em contrapropostas ou justificativas', verbose_name='Mensagem da Empresa')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Criado em')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Atualizado em')),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='custom_plan_requests', to='companies.company', verbose_name='Empresa')),
            ],
            options={
                'verbose_name': 'Solicitação de Plano Personalizado',
                'verbose_name_plural': 'Solicitações de Planos Personalizados',
                'ordering': ['-created_at'],
            },
        ),
    ]
