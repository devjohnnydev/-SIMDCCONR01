"""
Migration para criar o modelo PaymentOrder.
"""
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('companies', '0001_initial'),
        ('billing', '0002_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='PaymentOrder',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_yearly', models.BooleanField(default=False, verbose_name='Assinatura Anual')),
                ('status', models.CharField(choices=[
                    ('pending', 'Aguardando Pagamento'),
                    ('paid', 'Pago'),
                    ('failed', 'Falhou'),
                    ('cancelled', 'Cancelado'),
                ], default='pending', max_length=20, verbose_name='Status')),
                ('amount', models.IntegerField(default=0, help_text='Valor em centavos BRL', verbose_name='Valor (centavos)')),
                ('stripe_session_id', models.CharField(blank=True, db_index=True, max_length=255, verbose_name='Stripe Session ID')),
                ('stripe_payment_intent_id', models.CharField(blank=True, max_length=255, verbose_name='Stripe Payment Intent ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Criado em')),
                ('paid_at', models.DateTimeField(blank=True, null=True, verbose_name='Pago em')),
                ('company', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='payment_orders',
                    to='companies.company',
                    verbose_name='Empresa',
                )),
                ('plan', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='payment_orders',
                    to='billing.plan',
                    verbose_name='Plano',
                )),
            ],
            options={
                'verbose_name': 'Ordem de Pagamento',
                'verbose_name_plural': 'Ordens de Pagamento',
                'ordering': ['-created_at'],
                'indexes': [
                    models.Index(fields=['stripe_session_id'], name='billing_pay_stripe__idx'),
                ],
            },
        ),
    ]
