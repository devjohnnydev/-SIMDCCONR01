from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0003_report_updates'),
        ('accounts', '0004_user_professional_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='employeediagnostic',
            name='is_signed',
            field=models.BooleanField(default=False, verbose_name='Assinado'),
        ),
        migrations.AddField(
            model_name='employeediagnostic',
            name='signed_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='signed_diagnostics', to='accounts.user'),
        ),
        migrations.AddField(
            model_name='employeediagnostic',
            name='signature_method',
            field=models.CharField(blank=True, choices=[('INTERNAL', 'Interna'), ('GOVBR', 'Gov.br'), ('MANUAL', 'Manual')], max_length=20, verbose_name='Metodo de Assinatura'),
        ),
        migrations.AddField(
            model_name='employeediagnostic',
            name='signature_timestamp',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Data da Assinatura'),
        ),
        migrations.AddField(
            model_name='employeediagnostic',
            name='govbr_token',
            field=models.CharField(blank=True, max_length=255, verbose_name='Token Gov.br'),
        ),
    ]
