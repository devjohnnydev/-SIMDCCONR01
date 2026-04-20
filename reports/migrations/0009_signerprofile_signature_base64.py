from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0008_alter_signerprofile_signature_image'),
    ]

    operations = [
        migrations.AddField(
            model_name='signerprofile',
            name='signature_base64',
            field=models.TextField(
                blank=True,
                default='',
                help_text='Imagem da assinatura salva como data URI base64 para persistência',
                verbose_name='Assinatura (Base64)',
            ),
        ),
    ]
