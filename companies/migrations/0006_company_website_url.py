from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('companies', '0005_populate_logo_db'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                # Usa IF NOT EXISTS para evitar erro se a coluna já existir no Postgres
                migrations.RunSQL(
                    sql="ALTER TABLE companies_company ADD COLUMN IF NOT EXISTS website_url varchar(500);",
                    reverse_sql="ALTER TABLE companies_company DROP COLUMN IF EXISTS website_url;"
                ),
            ],
            state_operations=[
                migrations.AddField(
                    model_name='company',
                    name='website_url',
                    field=models.URLField(blank=True, max_length=500, null=True, verbose_name='URL do Sistema/Site'),
                ),
            ]
        ),
    ]
