from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_user_lgpd_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='professional_crp',
            field=models.CharField(blank=True, max_length=50, verbose_name='Registro CRP'),
        ),
        migrations.AddField(
            model_name='user',
            name='signature_image',
            field=models.ImageField(blank=True, null=True, upload_to='signatures/', verbose_name='Assinatura Digital'),
        ),
    ]
