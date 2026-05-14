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
    """Helper: retorna a empresa do usuário ou da sessão para admin_master."""
    if request.user.is_admin_master:
        # Prioridade 1: Parametro GET ou POST
        company_pk = request.GET.get('company') or request.POST.get('company')
        if company_pk:
            request.session['selected_company_id'] = str(company_pk)
            from companies.models import Company
            return get_object_or_404(Company, pk=company_pk)
            
        # Prioridade 2: Sessão
        session_company_id = request.session.get('selected_company_id')
        if session_company_id:
            from companies.models import Company
            company = Company.objects.filter(pk=session_company_id).first()
            if company:
                return company

        # Para admin_master sem company selecionada, usar a primeira ativa
        from companies.models import Company
        company = Company.objects.filter(status='ACTIVE').first()
        if company:
            request.session['selected_company_id'] = str(company.pk)
        return company
    return request.user.company


@login_required
def gro_dashboard(request):
    """Dashboard do ciclo GRO — visualização para empresa (somente leitura) e admin (completo)."""
    company = _get_company(request)
    if not company:
        messages.warning(request, 'Selecione uma empresa para visualizar o painel de riscos.')
        return redirect('companies:list') if request.user.is_admin_master else redirect('accounts:dashboard')

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

    # Perigos pendentes de revisão (auto-gerados)
    pending_review = hazards.filter(status='PENDING_REVIEW').count()

    # Pesquisas encerradas (para botão de geração automática)
    from forms_builder.models import FormInstance
    closed_forms = FormInstance.objects.filter(
        company=company, status='CLOSED'
    ).order_by('-created_at')[:5] if request.user.is_admin_master else []

    # Empresa vê o dashboard em modo somente-leitura (sem criar/editar perigos)
    is_readonly = not request.user.is_admin_master

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
        'is_readonly': is_readonly,
        'pending_review': pending_review,
        'closed_forms': closed_forms,
    }
    return render(request, 'risk_management/gro_dashboard.html', context)


@login_required
def hazard_list(request):
    """Lista de perigos — somente ADMIN_MASTER."""
    if not request.user.is_admin_master:
        messages.error(request, 'Acesso restrito ao administrador.')
        return redirect('risk_management:action_plan_list')

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
    """Cria novo registro de perigo — somente ADMIN_MASTER."""
    if not request.user.is_admin_master:
        messages.error(request, 'Acesso restrito ao administrador.')
        return redirect('risk_management:action_plan_list')

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
    """Edita um registro de perigo — somente ADMIN_MASTER."""
    if not request.user.is_admin_master:
        messages.error(request, 'Acesso restrito ao administrador.')
        return redirect('risk_management:action_plan_list')

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
    """Remove um perigo — somente ADMIN_MASTER."""
    if not request.user.is_admin_master:
        messages.error(request, 'Acesso restrito ao administrador.')
        return redirect('risk_management:action_plan_list')

    company = _get_company(request)
    hazard = get_object_or_404(HazardRegistry, pk=pk, company=company)
    if request.method == 'POST':
        desc = hazard.descricao_perigo[:60]
        hazard.delete()
        messages.success(request, f'Perigo "{desc}" removido.')
    return redirect('risk_management:hazard_list')


@login_required
def risk_assess(request, hazard_pk):
    """Avaliação de risco para um perigo — somente ADMIN_MASTER."""
    if not request.user.is_admin_master:
        messages.error(request, 'Acesso restrito ao administrador.')
        return redirect('risk_management:action_plan_list')

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
    """Visualização da Matriz de Risco 5×5 — somente ADMIN_MASTER."""
    if not request.user.is_admin_master:
        messages.error(request, 'Acesso restrito ao administrador.')
        return redirect('risk_management:action_plan_list')

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


@login_required
def approve_hazard(request, pk):
    """Aprova um perigo pendente de revisão — somente ADMIN_MASTER."""
    if not request.user.is_admin_master:
        messages.error(request, 'Acesso restrito ao administrador.')
        return redirect('risk_management:dashboard')

    company = _get_company(request)
    hazard = get_object_or_404(HazardRegistry, pk=pk, company=company, status='PENDING_REVIEW')

    if request.method == 'POST':
        hazard.status = 'ACTIVE'
        hazard.save(update_fields=['status', 'updated_at'])
        AuditLog.log(
            user=request.user, action='UPDATE',
            description=f'Perigo aprovado: {hazard.descricao_perigo[:60]}',
            obj=hazard, company=company, request=request
        )
        messages.success(request, f'Perigo "{hazard.source_dimension}" aprovado e visível para a empresa.')

    return redirect('risk_management:hazard_list')


@login_required
def reject_hazard(request, pk):
    """Rejeita (arquiva) um perigo pendente de revisão — somente ADMIN_MASTER."""
    if not request.user.is_admin_master:
        messages.error(request, 'Acesso restrito ao administrador.')
        return redirect('risk_management:dashboard')

    company = _get_company(request)
    hazard = get_object_or_404(HazardRegistry, pk=pk, company=company, status='PENDING_REVIEW')

    if request.method == 'POST':
        hazard.status = 'ELIMINATED'
        hazard.save(update_fields=['status', 'updated_at'])
        AuditLog.log(
            user=request.user, action='DELETE',
            description=f'Perigo rejeitado: {hazard.descricao_perigo[:60]}',
            obj=hazard, company=company, request=request
        )
        messages.success(request, f'Perigo "{hazard.source_dimension}" rejeitado.')

    return redirect('risk_management:hazard_list')


@login_required
def approve_all_hazards(request):
    """Aprova todos os perigos pendentes de uma pesquisa — somente ADMIN_MASTER."""
    if not request.user.is_admin_master:
        messages.error(request, 'Acesso restrito ao administrador.')
        return redirect('risk_management:dashboard')

    company = _get_company(request)

    if request.method == 'POST':
        pending = HazardRegistry.objects.filter(
            company=company, status='PENDING_REVIEW'
        )
        count = pending.count()
        pending.update(status='ACTIVE', updated_at=timezone.now())
        messages.success(request, f'{count} perigos aprovados com sucesso.')

    return redirect('risk_management:hazard_list')


@login_required
def generate_hazards_from_survey(request, form_pk):
    """Dispara a geração automática de perigos a partir de uma pesquisa — ADMIN_MASTER."""
    if not request.user.is_admin_master:
        messages.error(request, 'Acesso restrito ao administrador.')
        return redirect('risk_management:dashboard')

    from forms_builder.models import FormInstance
    form_instance = get_object_or_404(FormInstance, pk=form_pk)

    if request.method == 'POST':
        from .services import auto_generate_hazards
        result = auto_generate_hazards(form_instance, user=request.user)

        total = result['total_generated']
        skipped = result['total_skipped']

        if total > 0:
            messages.success(
                request,
                f'{total} perigo(s) gerado(s) automaticamente e aguardando sua revisão. '
                f'{skipped} já existiam.'
            )
        else:
            messages.info(
                request,
                'Nenhum novo perigo identificado. Todas as dimensões estão adequadas '
                'ou os perigos já foram gerados anteriormente.'
            )

    return redirect('risk_management:hazard_list')


@login_required
def compare_surveys_view(request):
    """Compara duas pesquisas da mesma empresa — ADMIN_MASTER."""
    if not request.user.is_admin_master:
        messages.error(request, 'Acesso restrito ao administrador.')
        return redirect('risk_management:dashboard')

    company = _get_company(request)
    if not company:
        return redirect('accounts:dashboard')

    from forms_builder.models import FormInstance

    # Pesquisas encerradas desta empresa
    closed_forms = FormInstance.objects.filter(
        company=company, status='CLOSED'
    ).order_by('-created_at')

    comparison = None
    current_pk = request.GET.get('current')
    previous_pk = request.GET.get('previous')

    if current_pk and previous_pk:
        current_form = get_object_or_404(FormInstance, pk=current_pk, company=company)
        previous_form = get_object_or_404(FormInstance, pk=previous_pk, company=company)

        from .services import compare_surveys
        comparison = compare_surveys(current_form, previous_form)

        # Se solicitado, atualizar perigos
        if request.GET.get('update_hazards') == '1':
            from .services import update_hazards_from_comparison
            updated = update_hazards_from_comparison(company, comparison, current_form, request.user)
            if updated:
                messages.success(request, f'{len(updated)} perigo(s) atualizado(s) com base na evolução.')
            comparison['hazards_updated'] = updated

    context = {
        'company': company,
        'closed_forms': closed_forms,
        'comparison': comparison,
        'current_pk': current_pk,
        'previous_pk': previous_pk,
    }
    return render(request, 'risk_management/compare_surveys.html', context)

