"""Views para Gestão de Riscos Ocupacionais (GRO)."""
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone
from django.http import JsonResponse

from .models import HazardRegistry, RiskAssessment, ControlMeasure, ActionPlan
from companies.views import require_company_admin, require_admin_master
from audit.models import AuditLog


def _get_company(request):
    """Helper: retorna a empresa do usuário ou None para admin_master."""
    if request.user.is_admin_master:
        # Prioridade 1: Parametro GET
        company_pk = request.GET.get('company') or request.POST.get('company')
        if company_pk:
            from companies.models import Company
            return get_object_or_404(Company, pk=company_pk)
        # Para admin_master sem company selecionada via GET, usar a primeira ativa
        from companies.models import Company
        return Company.objects.filter(status='ACTIVE').first()
    return request.user.company


@login_required
def gro_dashboard(request):
    """Dashboard do ciclo GRO: identificar → avaliar → controlar → acompanhar."""
    company = _get_company(request)
    if not company:
        messages.warning(request, 'Selecione uma empresa para visualizar o painel de riscos.')
        return redirect('companies:list')

    hazards = HazardRegistry.objects.filter(company=company)
    action_plans = ActionPlan.objects.filter(company=company)

    # Métricas
    total_hazards = hazards.count()
    active_hazards = hazards.filter(status='ACTIVE').count()
    mitigated = hazards.filter(status='MITIGATED').count()
    eliminated = hazards.filter(status='ELIMINATED').count()

    # Riscos por tipo
    risks_by_type = hazards.filter(status='ACTIVE').values(
        'tipo_risco'
    ).annotate(count=Count('id')).order_by('-count')

    # Riscos por nível (via assessment)
    from django.db.models import Subquery, OuterRef
    critical_count = RiskAssessment.objects.filter(
        hazard__company=company,
        hazard__status='ACTIVE',
        nivel_risco__in=['SUBSTANCIAL', 'INTOLERAVEL']
    ).count()

    # Planos de ação por status
    plans_by_status = action_plans.values('status').annotate(
        count=Count('id')
    )
    plans_dict = {p['status']: p['count'] for p in plans_by_status}

    overdue_plans = action_plans.filter(
        status__in=['PENDENTE', 'EM_ANDAMENTO'],
        prazo_fim__lt=timezone.now().date()
    ).count()

    companies_list = None
    if request.user.is_admin_master:
        from companies.models import Company
        companies_list = Company.objects.filter(status='ACTIVE')

    context = {
        'company': company,
        'total_hazards': total_hazards,
        'active_hazards': active_hazards,
        'mitigated': mitigated,
        'eliminated': eliminated,
        'critical_count': critical_count,
        'risks_by_type': json.dumps(list(risks_by_type)),
        'plans_pendente': plans_dict.get('PENDENTE', 0),
        'plans_andamento': plans_dict.get('EM_ANDAMENTO', 0),
        'plans_concluido': plans_dict.get('CONCLUIDO', 0),
        'overdue_plans': overdue_plans,
        'companies_list': companies_list,
    }
    return render(request, 'risk_management/gro_dashboard.html', context)


@login_required
def hazard_list(request):
    """Lista de perigos com filtros."""
    company = _get_company(request)
    if not company:
        return redirect('accounts:dashboard')

    hazards = HazardRegistry.objects.filter(
        company=company
    ).select_related('identified_by').order_by('-created_at')

    # Filtros
    tipo = request.GET.get('tipo')
    setor = request.GET.get('setor')
    status = request.GET.get('status')

    if tipo:
        hazards = hazards.filter(tipo_risco=tipo)
    if setor:
        hazards = hazards.filter(setor=setor)
    if status:
        hazards = hazards.filter(status=status)

    # Setores disponíveis para filtro
    setores = HazardRegistry.objects.filter(
        company=company
    ).values_list('setor', flat=True).distinct()

    context = {
        'hazards': hazards,
        'setores': setores,
        'filter_tipo': tipo,
        'filter_setor': setor,
        'filter_status': status,
        'company': company,
    }
    return render(request, 'risk_management/hazard_list.html', context)


@login_required
def hazard_create(request):
    """Cria novo registro de perigo."""
    company = _get_company(request)
    if not company:
        return redirect('accounts:dashboard')

    if request.method == 'POST':
        hazard = HazardRegistry.objects.create(
            company=company,
            setor=request.POST.get('setor', '').strip(),
            funcao=request.POST.get('funcao', '').strip(),
            atividade=request.POST.get('atividade', '').strip(),
            descricao_perigo=request.POST.get('descricao_perigo', '').strip(),
            fonte_geradora=request.POST.get('fonte_geradora', '').strip(),
            tipo_risco=request.POST.get('tipo_risco', 'PSICOSSOCIAL'),
            norma_referencia=request.POST.get('norma_referencia', 'NR-1'),
            identified_by=request.user,
        )
        AuditLog.log(
            user=request.user, action='CREATE',
            description=f'Perigo identificado: {hazard.descricao_perigo[:60]}',
            obj=hazard, company=company, request=request
        )
        messages.success(request, 'Perigo registrado com sucesso!')
        return redirect('risk_management:hazard_list')

    # Carregar setores e funções existentes para autocomplete
    from employees.models import Employee
    setores = Employee.objects.filter(
        company=company, status='ACTIVE'
    ).values_list('setor', flat=True).distinct()
    funcoes = Employee.objects.filter(
        company=company, status='ACTIVE'
    ).values_list('cargo', flat=True).distinct()

    return render(request, 'risk_management/hazard_form.html', {
        'company': company,
        'setores': setores,
        'funcoes': funcoes,
        'risk_types': HazardRegistry.RISK_TYPE_CHOICES,
        'norm_choices': HazardRegistry.NORM_CHOICES,
    })


@login_required
def hazard_edit(request, pk):
    """Edita um registro de perigo."""
    company = _get_company(request)
    hazard = get_object_or_404(HazardRegistry, pk=pk, company=company)

    if request.method == 'POST':
        hazard.setor = request.POST.get('setor', hazard.setor).strip()
        hazard.funcao = request.POST.get('funcao', hazard.funcao).strip()
        hazard.atividade = request.POST.get('atividade', hazard.atividade).strip()
        hazard.descricao_perigo = request.POST.get('descricao_perigo', hazard.descricao_perigo).strip()
        hazard.fonte_geradora = request.POST.get('fonte_geradora', hazard.fonte_geradora).strip()
        hazard.tipo_risco = request.POST.get('tipo_risco', hazard.tipo_risco)
        hazard.norma_referencia = request.POST.get('norma_referencia', hazard.norma_referencia)
        hazard.status = request.POST.get('status', hazard.status)
        hazard.save()
        messages.success(request, 'Perigo atualizado!')
        return redirect('risk_management:hazard_list')

    from employees.models import Employee
    setores = Employee.objects.filter(
        company=company, status='ACTIVE'
    ).values_list('setor', flat=True).distinct()
    funcoes = Employee.objects.filter(
        company=company, status='ACTIVE'
    ).values_list('cargo', flat=True).distinct()

    return render(request, 'risk_management/hazard_form.html', {
        'company': company,
        'hazard': hazard,
        'setores': setores,
        'funcoes': funcoes,
        'risk_types': HazardRegistry.RISK_TYPE_CHOICES,
        'norm_choices': HazardRegistry.NORM_CHOICES,
        'status_choices': HazardRegistry.STATUS_CHOICES,
        'editing': True,
    })


@login_required
def hazard_delete(request, pk):
    """Remove um perigo."""
    company = _get_company(request)
    hazard = get_object_or_404(HazardRegistry, pk=pk, company=company)
    if request.method == 'POST':
        desc = hazard.descricao_perigo[:60]
        hazard.delete()
        messages.success(request, f'Perigo "{desc}" removido.')
    return redirect('risk_management:hazard_list')


@login_required
def risk_assess(request, hazard_pk):
    """Avaliação de risco para um perigo (Probabilidade × Severidade)."""
    company = _get_company(request)
    hazard = get_object_or_404(HazardRegistry, pk=hazard_pk, company=company)

    if request.method == 'POST':
        assessment = RiskAssessment.objects.create(
            hazard=hazard,
            probabilidade=int(request.POST.get('probabilidade', 3)),
            severidade=int(request.POST.get('severidade', 3)),
            justificativa=request.POST.get('justificativa', ''),
            avaliado_por=request.user,
        )
        AuditLog.log(
            user=request.user, action='CREATE',
            description=f'Avaliação de risco: {assessment.nivel_risco} (score={assessment.score})',
            obj=assessment, company=company, request=request
        )
        messages.success(request, f'Risco avaliado: {assessment.get_nivel_risco_display()} (P{assessment.probabilidade}×S{assessment.severidade}={assessment.score})')
        return redirect('risk_management:hazard_list')

    existing_assessments = hazard.assessments.all()
    return render(request, 'risk_management/risk_assessment.html', {
        'hazard': hazard,
        'existing_assessments': existing_assessments,
        'company': company,
    })


@login_required
def risk_matrix_view(request):
    """Visualização da Matriz de Risco 5×5."""
    company = _get_company(request)
    if not company:
        return redirect('accounts:dashboard')

    assessments = RiskAssessment.objects.filter(
        hazard__company=company,
        hazard__status='ACTIVE'
    ).select_related('hazard')

    # Montar matrix 5×5
    matrix = {}
    for p in range(1, 6):
        for s in range(1, 6):
            matrix[f"{p}x{s}"] = []

    for a in assessments:
        key = f"{a.probabilidade}x{a.severidade}"
        matrix[key].append(a)

    return render(request, 'risk_management/risk_matrix.html', {
        'matrix': matrix,
        'company': company,
        'assessments': assessments,
    })


@login_required
def control_measures(request, assessment_pk):
    """Gerencia medidas de controle de uma avaliação de risco."""
    company = _get_company(request)
    assessment = get_object_or_404(
        RiskAssessment, pk=assessment_pk, hazard__company=company
    )

    if request.method == 'POST':
        ControlMeasure.objects.create(
            risk_assessment=assessment,
            tipo=request.POST.get('tipo', 'ADMINISTRATIVA'),
            descricao=request.POST.get('descricao', '').strip(),
            responsavel=request.POST.get('responsavel', '').strip(),
            prazo=request.POST.get('prazo') or None,
        )
        messages.success(request, 'Medida de controle adicionada!')
        return redirect('risk_management:control_measures', assessment_pk=assessment_pk)

    controls = assessment.control_measures.all()
    return render(request, 'risk_management/control_measures.html', {
        'assessment': assessment,
        'controls': controls,
        'hierarchy_choices': ControlMeasure.HIERARCHY_CHOICES,
        'company': company,
    })


@login_required
def toggle_control(request, pk):
    """Toggle implementação de uma medida de controle."""
    company = _get_company(request)
    control = get_object_or_404(
        ControlMeasure, pk=pk, risk_assessment__hazard__company=company
    )
    if request.method == 'POST':
        control.implementada = not control.implementada
        if control.implementada:
            control.data_implementacao = timezone.now().date()
        control.save()
    return redirect('risk_management:control_measures',
                    assessment_pk=control.risk_assessment.pk)


@login_required
def action_plan_list(request):
    """Lista de planos de ação."""
    company = _get_company(request)
    if not company:
        return redirect('accounts:dashboard')

    plans = ActionPlan.objects.filter(company=company)

    status_filter = request.GET.get('status')
    if status_filter:
        plans = plans.filter(status=status_filter)

    context = {
        'plans': plans,
        'company': company,
        'status_filter': status_filter,
        'status_choices': ActionPlan.STATUS_CHOICES,
    }
    return render(request, 'risk_management/action_plan_list.html', context)


@login_required
def action_plan_create(request):
    """Cria novo plano de ação."""
    company = _get_company(request)
    if not company:
        return redirect('accounts:dashboard')

    if request.method == 'POST':
        assessment_pk = request.POST.get('risk_assessment')
        assessment = None
        if assessment_pk:
            assessment = RiskAssessment.objects.filter(
                pk=assessment_pk, hazard__company=company
            ).first()

        plan = ActionPlan.objects.create(
            company=company,
            risk_assessment=assessment,
            titulo=request.POST.get('titulo', '').strip(),
            descricao=request.POST.get('descricao', '').strip(),
            responsavel=request.POST.get('responsavel', '').strip(),
            prioridade=request.POST.get('prioridade', 'MEDIA'),
            prazo_inicio=request.POST.get('prazo_inicio') or None,
            prazo_fim=request.POST.get('prazo_fim'),
            indicador_eficacia=request.POST.get('indicador_eficacia', ''),
            created_by=request.user,
        )
        messages.success(request, 'Plano de ação criado!')
        return redirect('risk_management:action_plan_list')

    assessments = RiskAssessment.objects.filter(
        hazard__company=company, hazard__status='ACTIVE'
    ).select_related('hazard')

    return render(request, 'risk_management/action_plan_form.html', {
        'company': company,
        'assessments': assessments,
        'priority_choices': ActionPlan.PRIORITY_CHOICES,
    })


@login_required
def action_plan_edit(request, pk):
    """Edita um plano de ação."""
    company = _get_company(request)
    plan = get_object_or_404(ActionPlan, pk=pk, company=company)

    if request.method == 'POST':
        plan.titulo = request.POST.get('titulo', plan.titulo).strip()
        plan.descricao = request.POST.get('descricao', plan.descricao).strip()
        plan.responsavel = request.POST.get('responsavel', plan.responsavel).strip()
        plan.prioridade = request.POST.get('prioridade', plan.prioridade)
        plan.prazo_fim = request.POST.get('prazo_fim', plan.prazo_fim)
        plan.indicador_eficacia = request.POST.get('indicador_eficacia', plan.indicador_eficacia)
        plan.percentual_conclusao = int(request.POST.get('percentual_conclusao', plan.percentual_conclusao))
        plan.save()
        messages.success(request, 'Plano de ação atualizado!')
        return redirect('risk_management:action_plan_list')

    return render(request, 'risk_management/action_plan_form.html', {
        'company': company,
        'plan': plan,
        'editing': True,
        'priority_choices': ActionPlan.PRIORITY_CHOICES,
    })


@login_required
def action_plan_status(request, pk):
    """Atualiza status de um plano de ação."""
    company = _get_company(request)
    plan = get_object_or_404(ActionPlan, pk=pk, company=company)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(ActionPlan.STATUS_CHOICES):
            plan.status = new_status
            if new_status == 'CONCLUIDO':
                plan.data_conclusao = timezone.now().date()
                plan.percentual_conclusao = 100
            plan.save()
            messages.success(request, f'Status atualizado para {plan.get_status_display()}!')
    return redirect('risk_management:action_plan_list')
