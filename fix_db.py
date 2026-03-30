import os
import django
from django.db import connection

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'saas_nr01.settings')
django.setup()

def execute(sql):
    with connection.cursor() as cursor:
        try:
            cursor.execute(sql)
            print("OK:", sql)
        except Exception as e:
            print("Skipped/Err:", sql, "->", e)

print("Forcing safety columns on accounts_user...")
execute("ALTER TABLE accounts_user ADD COLUMN IF NOT EXISTS company_id integer;")
execute("ALTER TABLE accounts_user ADD COLUMN IF NOT EXISTS lgpd_individual_accepted boolean DEFAULT false;")
execute("ALTER TABLE accounts_user ADD COLUMN IF NOT EXISTS lgpd_individual_at timestamp with time zone;")
execute("ALTER TABLE accounts_user ADD COLUMN IF NOT EXISTS lgpd_aggregate_accepted boolean DEFAULT false;")
execute("ALTER TABLE accounts_user ADD COLUMN IF NOT EXISTS lgpd_aggregate_at timestamp with time zone;")
execute("ALTER TABLE accounts_user ADD COLUMN IF NOT EXISTS terms_accepted boolean DEFAULT false;")
execute("ALTER TABLE accounts_user ADD COLUMN IF NOT EXISTS terms_accepted_at timestamp with time zone;")
execute("ALTER TABLE accounts_user ADD COLUMN IF NOT EXISTS privacy_accepted boolean DEFAULT false;")
execute("ALTER TABLE accounts_user ADD COLUMN IF NOT EXISTS privacy_accepted_at timestamp with time zone;")
print("Safety columns check complete.")
