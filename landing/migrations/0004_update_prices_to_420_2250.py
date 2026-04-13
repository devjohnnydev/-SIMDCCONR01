from django.db import migrations

def update_prices(apps, schema_editor):
    LandingConfig = apps.get_model('landing', 'LandingConfig')
    config, created = LandingConfig.objects.get_or_create(id=1)
    config.starter_price = 420
    config.pro_price = 2250
    config.save()

class Migration(migrations.Migration):

    dependencies = [
        ('landing', '0003_alter_landingconfig_pro_price_and_more'),
    ]

    operations = [
        migrations.RunPython(update_prices),
    ]
