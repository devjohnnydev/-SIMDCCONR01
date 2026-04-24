from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('landing', '0004_update_prices_to_420_2250'),
    ]

    operations = [
        migrations.AddField(
            model_name='landingconfig',
            name='hero_image_db',
            field=models.BinaryField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='landingconfig',
            name='hero_image_mime',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='testimonial',
            name='avatar_db',
            field=models.BinaryField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='testimonial',
            name='avatar_mime',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
