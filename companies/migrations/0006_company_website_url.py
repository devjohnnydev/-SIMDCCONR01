from django.db import migrations, models, connection


def add_website_url_column(apps, schema_editor):
    """Adiciona coluna website_url de forma segura (compatível SQLite e Postgres)."""
    with connection.cursor() as cursor:
        # Verifica se a coluna já existe
        columns = [col.name for col in connection.introspection.get_table_description(cursor, 'companies_company')]
        if 'website_url' not in columns:
            cursor.execute("ALTER TABLE companies_company ADD COLUMN website_url varchar(500);")


def remove_website_url_column(apps, schema_editor):
    """Remove coluna website_url (apenas Postgres suporta DROP COLUMN)."""
    if connection.vendor != 'sqlite':
        with connection.cursor() as cursor:
            cursor.execute("ALTER TABLE companies_company DROP COLUMN IF EXISTS website_url;")


class Migration(migrations.Migration):

    dependencies = [
        ('companies', '0005_populate_logo_db'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunPython(add_website_url_column, remove_website_url_column),
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
