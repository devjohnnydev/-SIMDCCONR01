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
# Ensure table exists (though migration 0002 should have done this)
# We add every core field from the model to be safe against partial migrations.
execute("ALTER TABLE reports_employeediagnostic ADD COLUMN IF NOT EXISTS assignment_id integer;")
execute("ALTER TABLE reports_employeediagnostic ADD COLUMN IF NOT EXISTS validation_code uuid;")
execute("ALTER TABLE reports_employeediagnostic ADD COLUMN IF NOT EXISTS diagnostic_data jsonb DEFAULT '{}';")
execute("ALTER TABLE reports_employeediagnostic ADD COLUMN IF NOT EXISTS generated_at timestamp with time zone;")
execute("ALTER TABLE reports_employeediagnostic ADD COLUMN IF NOT EXISTS assigned_professional_id integer;")
execute("ALTER TABLE reports_employeediagnostic ADD COLUMN IF NOT EXISTS is_signed boolean DEFAULT false;")
execute("ALTER TABLE reports_employeediagnostic ADD COLUMN IF NOT EXISTS signed_by_id integer;")
execute("ALTER TABLE reports_employeediagnostic ADD COLUMN IF NOT EXISTS signature_method varchar(20) DEFAULT '';")
execute("ALTER TABLE reports_employeediagnostic ADD COLUMN IF NOT EXISTS signature_timestamp timestamp with time zone;")
execute("ALTER TABLE reports_employeediagnostic ADD COLUMN IF NOT EXISTS govbr_token varchar(255) DEFAULT '';")

print("Filling missing UUIDs for diagnostics...")
import uuid
with connection.cursor() as cursor:
    cursor.execute("SELECT id FROM reports_employeediagnostic WHERE validation_code IS NULL;")
    ids = cursor.fetchall()
    for row in ids:
        diag_id = row[0]
        new_uuid = str(uuid.uuid4())
        cursor.execute(f"UPDATE reports_employeediagnostic SET validation_code = '{new_uuid}' WHERE id = {diag_id};")
        print(f"Assigned UUID {new_uuid} to diagnostic {diag_id}")

print("Safety columns check complete.")
