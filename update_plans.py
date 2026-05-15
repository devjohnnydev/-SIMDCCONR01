"""
Script para atualizar os planos de pagamento no banco de dados.
Apaga planos antigos e cria os novos: Basic, Professional, Enterprise, Advanced.
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'saas_nr01.settings')
django.setup()

from billing.models import Plan
from decimal import Decimal

# Desativa todos os planos existentes (não deleta para preservar FK de Subscriptions)
Plan.objects.filter(is_active=True).update(is_active=False)

NR01_NOTE = "Importante: De acordo com a abrangência da NR01, estão sob sua responsabilidade os terceirizados, temporários e prestadores de serviços habituais que frequentam sua organização/localização."

# ─── BASIC ───
basic, _ = Plan.objects.update_or_create(
    name='Basic',
    defaults={
        'description': f'Para PMEs até 20 vidas. Diagnósticos integrados com IA e conformidade NR-01 para pequenas equipes. {NR01_NOTE}',
        'price_monthly': Decimal('200.00'),
        'price_yearly': None,
        'price_semestral': Decimal('1200.00'),
        'pricing_mode': 'FIXED',
        'default_billing_cycle': 'SEMESTRAL',
        'max_employees': 5,
        'max_forms': 10,
        'max_reports': 20,
        'data_retention_days': 365,
        'has_pdf_export': True,
        'has_csv_import': True,
        'has_api_access': False,
        'has_custom_branding': True,
        'has_priority_support': False,
        'is_active': True,
        'is_featured': False,
        'order': 1,
    }
)
print(f"[OK] Plano '{basic.name}' criado/atualizado: R$ {basic.price_monthly}/mes (ate {basic.max_employees} vidas)")

# ─── PROFESSIONAL ───
pro, _ = Plan.objects.update_or_create(
    name='Professional',
    defaults={
        'description': f'Para organizações de 6 a 30 colaboradores. Laudos periciais completos, rastreabilidade por CPF e suporte prioritário. {NR01_NOTE}',
        'price_monthly': Decimal('1100.00'),
        'price_yearly': None,
        'price_semestral': Decimal('6600.00'),
        'pricing_mode': 'FIXED',
        'default_billing_cycle': 'SEMESTRAL',
        'max_employees': 30,
        'max_forms': 20,
        'max_reports': 50,
        'data_retention_days': 730,
        'has_pdf_export': True,
        'has_csv_import': True,
        'has_api_access': False,
        'has_custom_branding': True,
        'has_priority_support': True,
        'is_active': True,
        'is_featured': True,
        'order': 2,
    }
)
print(f"[OK] Plano '{pro.name}' criado/atualizado: R$ {pro.price_monthly}/mes (ate {pro.max_employees} vidas)")

# ─── ENTERPRISE ───
enterprise, _ = Plan.objects.update_or_create(
    name='Enterprise',
    defaults={
        'description': f'Para grupos e conglomerados +300. De 31 a 100 vidas com laudos periciais completos e suporte dedicado. {NR01_NOTE}',
        'price_monthly': Decimal('2999.00'),
        'price_yearly': None,
        'price_semestral': Decimal('17994.00'),
        'pricing_mode': 'FIXED',
        'default_billing_cycle': 'SEMESTRAL',
        'max_employees': 100,
        'max_forms': 50,
        'max_reports': 100,
        'data_retention_days': 1095,
        'has_pdf_export': True,
        'has_csv_import': True,
        'has_api_access': False,
        'has_custom_branding': True,
        'has_priority_support': True,
        'is_active': True,
        'is_featured': False,
        'order': 3,
    }
)
print(f"[OK] Plano '{enterprise.name}' criado/atualizado: R$ {enterprise.price_monthly}/mes (ate {enterprise.max_employees} vidas)")

# ─── ADVANCED ───
advanced, _ = Plan.objects.update_or_create(
    name='Advanced',
    defaults={
        'description': f'Sob consulta. Colaboradores ilimitados, multi-empresa (CNPJ), API de integração, SLA e suporte dedicado. {NR01_NOTE}',
        'price_monthly': Decimal('3000.00'),
        'price_yearly': None,
        'price_semestral': Decimal('18000.00'),
        'pricing_mode': 'FIXED',
        'default_billing_cycle': 'SEMESTRAL',
        'max_employees': 9999,
        'max_forms': 999,
        'max_reports': 999,
        'data_retention_days': 1825,
        'has_pdf_export': True,
        'has_csv_import': True,
        'has_api_access': True,
        'has_custom_branding': True,
        'has_priority_support': True,
        'is_active': True,
        'is_featured': False,
        'order': 4,
    }
)
print(f"[OK] Plano '{advanced.name}' criado/atualizado: a partir de R$ {advanced.price_monthly}/mes (ilimitado)")

print(f"\nTotal de planos ativos: {Plan.objects.filter(is_active=True).count()}")
