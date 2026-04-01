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
execute("ALTER TABLE accounts_user ADD COLUMN IF NOT EXISTS professional_crp varchar(50) DEFAULT '';")
execute("ALTER TABLE accounts_user ADD COLUMN IF NOT EXISTS signature_image varchar(100);")

print("Forcing safety columns on reports_employeediagnostic...")
# Ensure table exists first if possible, though migration 0002 should have created it.
# We focus on adding the columns that might be missing from faked migrations.
execute("ALTER TABLE reports_employeediagnostic ADD COLUMN IF NOT EXISTS assigned_professional_id integer;")
execute("ALTER TABLE reports_employeediagnostic ADD COLUMN IF NOT EXISTS is_signed boolean DEFAULT false;")
execute("ALTER TABLE reports_employeediagnostic ADD COLUMN IF NOT EXISTS signed_by_id integer;")
execute("ALTER TABLE reports_employeediagnostic ADD COLUMN IF NOT EXISTS signature_method varchar(20) DEFAULT '';")
execute("ALTER TABLE reports_employeediagnostic ADD COLUMN IF NOT EXISTS signature_timestamp timestamp with time zone;")
execute("ALTER TABLE reports_employeediagnostic ADD COLUMN IF NOT EXISTS govbr_token varchar(255) DEFAULT '';")

print("Safety columns check complete.")
