"""Views para Evolução e Inteligência — comparação histórica e score de risco."""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Avg
import json

from .models import EvolutionSnapshot, RiskScoreHistory, DimensionEvolution


def _get_company(request):
    if request.user.is_admin_master:
        from companies.models import Company
        company_pk = request.GET.get('company')
        if company_pk:
            return get_object_or_404(Company, pk=company_pk)
        return Company.objects.filter(status='ACTIVE').first()
    return request.user.company


@login_required
def evolution_dashboard(request):
    """Dashboard de evolução com gráficos e indicadores de tendência."""
    company = _get_company(request)
    if not company:
        from django.contrib import messages
        messages.warning(request, 'Selecione uma empresa para visualizar a evolução.')
        return redirect('companies:list')

    # Buscar snapshots (mais recente primeiro)
    snapshots = EvolutionSnapshot.objects.filter(
        company=company
    ).order_by('-snapshot_date')

    current_snapshot = snapshots.first()
    previous_snapshot = snapshots[1] if snapshots.count() > 1 else None

    # Comparação entre snapshots
    comparison = {}
    if current_snapshot and previous_snapshot:
        comparison = current_snapshot.compare_with(previous_snapshot)

    # Dados para gráfico de evolução temporal
    chart_labels = []
    chart_scores = []
    for snap in snapshots.order_by('snapshot_date')[:12]:
        chart_labels.append(snap.snapshot_date.strftime('%b/%Y'))
        chart_scores.append(float(snap.overall_score))

    # Risk score history
    risk_scores = RiskScoreHistory.objects.filter(
        company=company
    ).order_by('date')[:12]

    risk_scores_list = list(risk_scores)
    risk_labels = [r.date.strftime('%b/%Y') for r in risk_scores_list]
    risk_values = [r.score for r in risk_scores_list]
    current_risk = risk_scores_list[-1] if risk_scores_list else None

    # Evolução por dimensão (últimos snapshots)
    dimension_evolutions = DimensionEvolution.objects.filter(
        company=company
    ).order_by('-date')[:50]

    # Agrupar por dimensão para mini-gráficos
    dims_data = {}
    for de in dimension_evolutions:
        key = f"{de.instrumento}|{de.dimensao}"
        if key not in dims_data:
            dims_data[key] = {
                'instrumento': de.instrumento,
                'dimensao': de.dimensao,
                'values': [],
                'dates': [],
                'current': float(de.media),
                'classification': de.classificacao,
            }
        dims_data[key]['values'].insert(0, float(de.media))
        dims_data[key]['dates'].insert(0, de.date.strftime('%b/%y'))

    # Evolução por setor
    sector_data = {}
    if current_snapshot and current_snapshot.sector_scores:
        sector_data = current_snapshot.sector_scores
    prev_sector_data = {}
    if previous_snapshot and previous_snapshot.sector_scores:
        prev_sector_data = previous_snapshot.sector_scores

    sector_comparison = {}
    for sector, score in sector_data.items():
        prev = prev_sector_data.get(sector)
        if prev:
            diff = float(score) - float(prev)
            if diff > 0.2:
                trend = 'improved'
                icon = '🔼'
            elif diff < -0.2:
                trend = 'declined'
                icon = '🔽'
            else:
                trend = 'stable'
                icon = '➖'
        else:
            diff = 0
            trend = 'new'
            icon = '🆕'
        sector_comparison[sector] = {
            'current': float(score),
            'previous': float(prev) if prev else None,
            'diff': round(diff, 2),
            'trend': trend,
            'icon': icon,
        }

    # Empresas (para admin_master selecionar)
    companies_list = None
    if request.user.is_admin_master:
        from companies.models import Company
        companies_list = Company.objects.filter(status='ACTIVE')

    context = {
        'company': company,
        'companies_list': companies_list,
        'snapshots': snapshots[:10],
        'current_snapshot': current_snapshot,
        'previous_snapshot': previous_snapshot,
        'comparison': comparison,
        'chart_labels': json.dumps(chart_labels),
        'chart_scores': json.dumps(chart_scores),
        'risk_labels': json.dumps(risk_labels),
        'risk_values': json.dumps(risk_values),
        'current_risk': current_risk,
        'dims_data': dims_data,
        'sector_comparison': sector_comparison,
    }
    return render(request, 'evolution/dashboard.html', context)


@login_required
def compare_snapshots(request, snapshot_a, snapshot_b):
    """Comparação lado a lado entre dois snapshots."""
    company = _get_company(request)
    snap_a = get_object_or_404(EvolutionSnapshot, pk=snapshot_a, company=company)
    snap_b = get_object_or_404(EvolutionSnapshot, pk=snapshot_b, company=company)

    comparison = snap_a.compare_with(snap_b)

    return render(request, 'evolution/compare.html', {
        'snap_a': snap_a,
        'snap_b': snap_b,
        'comparison': comparison,
        'company': company,
    })


@login_required
def risk_score_timeline(request):
    """Linha do tempo do Score de Risco da empresa."""
    company = _get_company(request)
    if not company:
        return redirect('accounts:dashboard')

    history = RiskScoreHistory.objects.filter(company=company).order_by('date')
    current = history.last()

    chart_labels = [h.date.strftime('%d/%m/%Y') for h in history]
    chart_scores = [h.score for h in history]
    chart_types = json.dumps({
        'fisico': [h.score_fisico for h in history],
        'quimico': [h.score_quimico for h in history],
        'biologico': [h.score_biologico for h in history],
        'ergonomico': [h.score_ergonomico for h in history],
        'psicossocial': [h.score_psicossocial for h in history],
    })

    return render(request, 'evolution/risk_score.html', {
        'company': company,
        'history': history,
        'current': current,
        'chart_labels': json.dumps(chart_labels),
        'chart_scores': json.dumps(chart_scores),
        'chart_types': chart_types,
    })


@login_required
def dimension_detail(request, instrumento, dimensao):
    """Evolução detalhada de uma dimensão específica."""
    company = _get_company(request)
    if not company:
        return redirect('accounts:dashboard')

    evolutions = DimensionEvolution.objects.filter(
        company=company,
        instrumento=instrumento,
        dimensao=dimensao,
    ).order_by('date')

    chart_labels = [e.date.strftime('%b/%Y') for e in evolutions]
    chart_values = [float(e.media) for e in evolutions]

    return render(request, 'evolution/dimension_detail.html', {
        'company': company,
        'instrumento': instrumento,
        'dimensao': dimensao,
        'evolutions': evolutions,
        'chart_labels': json.dumps(chart_labels),
        'chart_values': json.dumps(chart_values),
    })


@login_required
def chart_data_api(request, company_pk):
    """API JSON para gráficos dinâmicos."""
    from companies.models import Company
    company = get_object_or_404(Company, pk=company_pk)

    if not request.user.is_admin_master and request.user.company != company:
        return JsonResponse({'error': 'Acesso negado'}, status=403)

    snapshots = EvolutionSnapshot.objects.filter(
        company=company
    ).order_by('snapshot_date')

    data = {
        'labels': [s.snapshot_date.strftime('%b/%Y') for s in snapshots],
        'scores': [float(s.overall_score) for s in snapshots],
        'classifications': [s.overall_classification for s in snapshots],
        'respondents': [s.total_respondentes for s in snapshots],
    }
    return JsonResponse(data)


@login_required
def sector_evolution(request):
    """Evolução por setor — comparação entre laudos para cada departamento."""
    company = _get_company(request)
    if not company:
        return redirect('accounts:dashboard')

    snapshots = EvolutionSnapshot.objects.filter(
        company=company
    ).order_by('snapshot_date')

    # Construir histórico por setor
    sectors = {}
    for snap in snapshots:
        if snap.sector_scores:
            for sector, score in snap.sector_scores.items():
                if sector not in sectors:
                    sectors[sector] = {'labels': [], 'scores': [], 'current': 0}
                sectors[sector]['labels'].append(snap.snapshot_date.strftime('%b/%Y'))
                sectors[sector]['scores'].append(float(score))
                sectors[sector]['current'] = float(score)

    # Calcular tendência para cada setor
    for sector, data in sectors.items():
        scores = data['scores']
        if len(scores) >= 2:
            diff = scores[-1] - scores[-2]
            if diff > 0.2:
                data['trend'] = 'improved'
                data['icon'] = '🔼'
            elif diff < -0.2:
                data['trend'] = 'declined'
                data['icon'] = '🔽'
            else:
                data['trend'] = 'stable'
                data['icon'] = '➖'
            data['diff'] = round(diff, 2)
        else:
            data['trend'] = 'new'
            data['icon'] = '🆕'
            data['diff'] = 0

    # Empresas para admin_master
    companies_list = None
    if request.user.is_admin_master:
        from companies.models import Company
        companies_list = Company.objects.filter(status='ACTIVE')

    context = {
        'company': company,
        'companies_list': companies_list,
        'sectors': sectors,
        'sectors_json': json.dumps({
            k: {'labels': v['labels'], 'scores': v['scores']}
            for k, v in sectors.items()
        }),
        'total_snapshots': snapshots.count(),
    }
    return render(request, 'evolution/sector_evolution.html', context)


@login_required
def employee_evolution(request, employee_pk=None):
    """
    Evolução individual de um funcionário — todos os laudos e scores.
    Admin Master pode ver qualquer funcionário; Company Admin da própria empresa.
    """
    from employees.models import Employee
    from forms_builder.models import FormAssignment, FormAnswer
    from reports.models import EmployeeDiagnostic

    company = _get_company(request)
    if not company:
        return redirect('accounts:dashboard')

    # Lista de funcionários para seleção
    employees = Employee.objects.filter(company=company, status='ACTIVE').order_by('nome')

    selected_employee = None
    employee_data = {}

    if employee_pk:
        selected_employee = get_object_or_404(Employee, pk=employee_pk, company=company)

        # Buscar todos os assignments completados
        assignments = FormAssignment.objects.filter(
            employee=selected_employee,
            status='COMPLETED',
        ).select_related('form_instance', 'form_instance__template').order_by('-completed_at')

        # Para cada assignment, calcular score médio das respostas
        history = []
        for assign in assignments:
            answers = FormAnswer.objects.filter(
                assignment=assign,
                question__question_type__in=['SCALE', 'SCALE_10']
            )

            scores = []
            if answers.exists():
                for answer in answers:
                    try:
                        if answer.numeric_value is not None:
                            val = float(answer.numeric_value)
                            scores.append(val)
                    except (ValueError, TypeError):
                        pass

            if scores:
                avg = sum(scores) / len(scores)
                # Classificar
                if avg <= 2.4:
                    classification = 'Crítico'
                elif avg <= 3.4:
                    classification = 'Atenção'
                elif avg <= 4.2:
                    classification = 'Adequado'
                else:
                    classification = 'Forte'
            else:
                avg = 0
                classification = 'N/A'

            # Verificar se tem diagnóstico IA
            has_diagnostic = hasattr(assign, 'diagnostic')
            is_signed = False
            validation_code = None
            if has_diagnostic:
                validation_code = assign.diagnostic.validation_code
                is_signed = assign.diagnostic.is_signed

            # Só exibe se houver notas numéricas OU se possuir laudo (diagnostic)
            if scores or has_diagnostic:
                history.append({
                    'date': assign.completed_at.strftime('%d/%m/%Y') if assign.completed_at else 'N/A',
                    'form_name': assign.form_instance.title,
                    'avg_score': round(avg, 2) if scores else 'N/A',
                    'classification': classification,
                    'total_answers': len(scores),
                    'has_diagnostic': has_diagnostic,
                    'is_signed': is_signed,
                    'validation_code': validation_code,
                    'assignment_pk': assign.pk,
                })

        # Filtrar laudos assinados
        signed_diagnostics = [h for h in history if h.get('has_diagnostic') and h.get('is_signed')]

        employee_data = {
            'history': history,
            'signed_diagnostics': signed_diagnostics,
            'chart_labels': json.dumps([h['date'] for h in history]),
            'chart_scores': json.dumps([h['avg_score'] if h['avg_score'] != 'N/A' else None for h in history]),
        }

    # Admin pode ver todas as empresas
    companies_list = None
    if request.user.is_admin_master:
        from companies.models import Company
        companies_list = Company.objects.filter(status='ACTIVE')

    context = {
        'company': company,
        'companies_list': companies_list,
        'employees': employees,
        'selected_employee': selected_employee,
        'employee_data': employee_data,
    }
    return render(request, 'evolution/employee_evolution.html', context)


@login_required
def all_companies_evolution(request):
    """Visão consolidada de evolução de TODAS as empresas — apenas Admin Master."""
    if not request.user.is_admin_master:
        from django.contrib import messages
        messages.error(request, 'Acesso restrito.')
        return redirect('accounts:dashboard')

    from companies.models import Company

    companies = Company.objects.filter(status='ACTIVE')
    company_data = []

    for company in companies:
        snaps = EvolutionSnapshot.objects.filter(company=company).order_by('-snapshot_date')
        current = snaps.first()
        previous = snaps[1] if snaps.count() > 1 else None

        if current:
            diff = 0
            trend = 'new'
            icon = '🆕'
            if previous:
                diff = float(current.overall_score) - float(previous.overall_score)
                if diff > 0.2:
                    trend = 'improved'
                    icon = '🔼'
                elif diff < -0.2:
                    trend = 'declined'
                    icon = '🔽'
                else:
                    trend = 'stable'
                    icon = '➖'

            company_data.append({
                'company': company,
                'current_score': float(current.overall_score),
                'classification': current.overall_classification,
                'respondentes': current.total_respondentes,
                'last_date': current.snapshot_date,
                'diff': round(diff, 2),
                'trend': trend,
                'icon': icon,
                'total_snapshots': snaps.count(),
            })

    # Ordenar por score (pior primeiro)
    company_data.sort(key=lambda x: x['current_score'])

    context = {
        'company_data': company_data,
        'total_companies': len(company_data),
    }
    return render(request, 'evolution/all_companies.html', context)
