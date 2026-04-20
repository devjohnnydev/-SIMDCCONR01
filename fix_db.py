import os
import django
from django.db import connection

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'saas_nr01.settings')
django.setup()

def execute(sql):
    with connection.cursor() as cursor:
        try:
            cursor.execute(sql)
            print("OK:", sql[:100] + ("..." if len(sql) > 100 else ""))
        except Exception as e:
            print("Skipped/Err:", sql[:100], "->", e)

print("--- FORCING SAFETY COLUMNS ON accounts_user ---")
execute("ALTER TABLE accounts_user ADD COLUMN IF NOT EXISTS role varchar(20) DEFAULT 'EMPLOYEE';")
execute("ALTER TABLE accounts_user ADD COLUMN IF NOT EXISTS is_staff boolean DEFAULT false;")
execute("ALTER TABLE accounts_user ADD COLUMN IF NOT EXISTS is_active boolean DEFAULT true;")
execute("ALTER TABLE accounts_user ADD COLUMN IF NOT EXISTS date_joined timestamp with time zone DEFAULT NOW();")
execute("ALTER TABLE accounts_user ADD COLUMN IF NOT EXISTS company_id bigint;")
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

print("\n--- FORCING SAFETY COLUMNS ON companies_company ---")
# Basic fields that might be missing due to faked migrations
execute("ALTER TABLE companies_company ADD COLUMN IF NOT EXISTS logo varchar(100);")
execute("ALTER TABLE companies_company ADD COLUMN IF NOT EXISTS cor_primaria varchar(7) DEFAULT '#0d6efd';")
execute("ALTER TABLE companies_company ADD COLUMN IF NOT EXISTS cor_secundaria varchar(7) DEFAULT '#6c757d';")
execute("ALTER TABLE companies_company ADD COLUMN IF NOT EXISTS status varchar(20) DEFAULT 'PENDING';")
execute("ALTER TABLE companies_company ADD COLUMN IF NOT EXISTS plan_id bigint;")
execute("ALTER TABLE companies_company ADD COLUMN IF NOT EXISTS stripe_customer_id varchar(100) DEFAULT '';")
execute("ALTER TABLE companies_company ADD COLUMN IF NOT EXISTS stripe_subscription_id varchar(100) DEFAULT '';")
execute("ALTER TABLE companies_company ADD COLUMN IF NOT EXISTS subscription_status varchar(50) DEFAULT 'inactive';")
execute("ALTER TABLE companies_company ADD COLUMN IF NOT EXISTS current_period_end timestamp with time zone;")
execute("ALTER TABLE companies_company ADD COLUMN IF NOT EXISTS custom_price_monthly decimal(10,2);")
execute("ALTER TABLE companies_company ADD COLUMN IF NOT EXISTS custom_price_yearly decimal(10,2);")
execute("ALTER TABLE companies_company ADD COLUMN IF NOT EXISTS contratante_nome varchar(200);")
execute("ALTER TABLE companies_company ADD COLUMN IF NOT EXISTS contratante_documento varchar(20);")
execute("ALTER TABLE companies_company ADD COLUMN IF NOT EXISTS data_aceite_contrato timestamp with time zone;")

print("\n--- FORCING SAFETY TABLE: billing_plan ---")
execute("""
    CREATE TABLE IF NOT EXISTS billing_plan (
        id bigserial PRIMARY KEY,
        name varchar(100) NOT NULL,
        description text DEFAULT '',
        price_monthly decimal(10,2) NOT NULL DEFAULT 0,
        price_yearly decimal(10,2),
        max_employees integer DEFAULT 50,
        max_forms integer DEFAULT 10,
        max_reports integer DEFAULT 20,
        data_retention_days integer DEFAULT 365,
        has_pdf_export boolean DEFAULT true,
        has_csv_import boolean DEFAULT true,
        has_api_access boolean DEFAULT false,
        has_custom_branding boolean DEFAULT true,
        has_priority_support boolean DEFAULT false,
        is_active boolean DEFAULT true,
        is_featured boolean DEFAULT false,
        "order" integer DEFAULT 0,
        created_at timestamp with time zone NOT NULL DEFAULT NOW(),
        updated_at timestamp with time zone NOT NULL DEFAULT NOW()
    );
""")

print("\n--- FORCING SAFETY TABLE: audit_auditlog ---")
execute("""
    CREATE TABLE IF NOT EXISTS audit_auditlog (
        id bigserial PRIMARY KEY,
        action varchar(20) NOT NULL,
        description text NOT NULL,
        object_id integer CHECK (object_id >= 0),
        ip_address inet,
        user_agent text NOT NULL DEFAULT '',
        extra_data jsonb NOT NULL DEFAULT '{}',
        created_at timestamp with time zone NOT NULL DEFAULT NOW(),
        company_id bigint,
        content_type_id integer,
        user_id bigint
    );
""")

print("\n--- FORCING SAFETY COLUMNS ON reports_employeediagnostic ---")
execute("ALTER TABLE reports_employeediagnostic ADD COLUMN IF NOT EXISTS assignment_id bigint;")
execute("ALTER TABLE reports_employeediagnostic ADD COLUMN IF NOT EXISTS validation_code uuid;")
execute("ALTER TABLE reports_employeediagnostic ADD COLUMN IF NOT EXISTS diagnostic_data jsonb DEFAULT '{}';")
execute("ALTER TABLE reports_employeediagnostic ADD COLUMN IF NOT EXISTS generated_at timestamp with time zone DEFAULT NOW();")
execute("ALTER TABLE reports_employeediagnostic ADD COLUMN IF NOT EXISTS assigned_professional_id bigint;")
execute("ALTER TABLE reports_employeediagnostic ADD COLUMN IF NOT EXISTS is_signed boolean DEFAULT false;")
execute("ALTER TABLE reports_employeediagnostic ADD COLUMN IF NOT EXISTS signed_by_id bigint;")
execute("ALTER TABLE reports_employeediagnostic ADD COLUMN IF NOT EXISTS signature_method varchar(20) DEFAULT '';")
execute("ALTER TABLE reports_employeediagnostic ADD COLUMN IF NOT EXISTS signature_timestamp timestamp with time zone;")
execute("ALTER TABLE reports_employeediagnostic ADD COLUMN IF NOT EXISTS govbr_token varchar(255) DEFAULT '';")
execute("ALTER TABLE reports_employeediagnostic ADD COLUMN IF NOT EXISTS signer_profile_id bigint;")

print("\n--- FILLING MISSING UUIDS ---")
import uuid
with connection.cursor() as cursor:
    cursor.execute("""
        DELETE FROM reports_employeediagnostic a 
        WHERE a.id > (
            SELECT MIN(b.id) FROM reports_employeediagnostic b 
            WHERE a.assignment_id = b.assignment_id
        );
    """)
    cursor.execute("SELECT id FROM reports_employeediagnostic WHERE validation_code IS NULL;")
    ids = cursor.fetchall()
    for row in ids:
        diag_id = row[0]
        new_uuid = str(uuid.uuid4())
        cursor.execute(f"UPDATE reports_employeediagnostic SET validation_code = '{new_uuid}' WHERE id = {diag_id};")
        print(f"Assigned UUID {new_uuid} to diagnostic {diag_id}")

print("\n--- FORCING SAFETY TABLE: reports_signerprofile ---")
execute("""
    CREATE TABLE IF NOT EXISTS reports_signerprofile (
        id bigserial PRIMARY KEY,
        nome_completo varchar(200) NOT NULL,
        registro_profissional varchar(50) NOT NULL DEFAULT '',
        especialidade varchar(30) NOT NULL DEFAULT 'PSICOLOGO',
        email varchar(254) NOT NULL DEFAULT '',
        govbr_cpf varchar(11) NOT NULL DEFAULT '',
        signature_image varchar(100),
        is_active boolean NOT NULL DEFAULT true,
        created_at timestamp with time zone NOT NULL DEFAULT NOW()
    );
""")
execute("ALTER TABLE reports_signerprofile ADD COLUMN IF NOT EXISTS signature_base64 text;")

print("\n--- FORCING SAFETY COLUMNS ON forms_builder_formquestion ---")
execute("ALTER TABLE forms_builder_formquestion ADD COLUMN IF NOT EXISTS analysis_category varchar(20) DEFAULT 'DIAGNOSTICO';")

print("\n--- FORCING SAFETY TABLE: reports_departmentdiagnostic ---")
execute("""
    CREATE TABLE IF NOT EXISTS reports_departmentdiagnostic (
        id bigserial PRIMARY KEY,
        setor varchar(100) NOT NULL,
        diagnostic_data jsonb NOT NULL DEFAULT '{}',
        generated_at timestamp with time zone NOT NULL DEFAULT NOW(),
        company_id bigint NOT NULL,
        form_instance_id bigint NOT NULL,
        generated_by_id bigint,
        UNIQUE (company_id, setor, form_instance_id)
    );
""")

print("\nSafety check complete.")
