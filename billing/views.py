"""
Views para visualizacao de planos e limites.
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import Plan, Subscription
from companies.views import require_company_admin, require_admin_master


@login_required
@require_company_admin
def plan_current(request):
    """Exibe o plano atual da empresa."""
    company = request.user.company
    
    all_plans = Plan.objects.filter(is_active=True).order_by('order')
    
    usage = {
        'employees': company.get_employee_count(),
        'forms': company.get_active_forms_count(),
    }
    
    limits = None
    if company.plan:
        limits = {
            'max_employees': company.plan.max_employees,
            'max_forms': company.plan.max_forms,
            'employees_percent': round((usage['employees'] / company.plan.max_employees) * 100, 1),
            'forms_percent': round((usage['forms'] / company.plan.max_forms) * 100, 1),
        }
    
    context = {
        'company': company,
        'current_plan': company.plan,
        'all_plans': all_plans,
        'usage': usage,
        'limits': limits,
    }
    
    return render(request, 'billing/plan_current.html', context)


@login_required
@require_admin_master
def plan_list(request):
    """Lista todos os planos (ADMIN_MASTER)."""
    plans = Plan.objects.all().order_by('order')
    return render(request, 'billing/plan_list.html', {'plans': plans})


@login_required
def plan_pricing(request):
    """Pagina publica de precos."""
    plans = Plan.objects.filter(is_active=True).order_by('order')
    return render(request, 'billing/pricing.html', {'plans': plans})
