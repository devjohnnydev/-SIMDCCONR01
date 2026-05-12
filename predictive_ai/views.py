"""Views para IA Preditiva e Sugestões Automáticas."""
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone

from .models import PredictiveAlert, NRSuggestion
from .services import run_predictive_analysis, get_suggestions_for_risk


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
def predictive_dashboard(request):
    """Dashboard de IA Preditiva com alertas e tendências."""
    company = _get_company(request)
    if not company:
        return redirect('accounts:dashboard')

    if request.user.is_admin_master:
        alerts = PredictiveAlert.objects.all().order_by('-created_at')[:50]
    else:
        alerts = PredictiveAlert.objects.filter(
            company=company
        ).order_by('-created_at')[:30]

    # Separar por tipo
    sector_alerts = [a for a in alerts if a.trend_type == 'SECTOR_DECLINE']
    risk_alerts = [a for a in alerts if a.trend_type == 'RISK_GROWING']
    dimension_alerts = [a for a in alerts if a.trend_type == 'DIMENSION_ALERT']

    # Empresas para filtro (admin_master)
    companies_list = None
    if request.user.is_admin_master:
        from companies.models import Company
        companies_list = Company.objects.filter(status='ACTIVE')

    context = {
        'company': company,
        'companies_list': companies_list,
        'alerts': alerts,
        'sector_alerts': sector_alerts,
        'risk_alerts': risk_alerts,
        'dimension_alerts': dimension_alerts,
        'total_alerts': len(alerts),
        'unacknowledged': sum(1 for a in alerts if not a.is_acknowledged),
    }
    return render(request, 'predictive_ai/dashboard.html', context)


@login_required
def acknowledge_alert(request, pk):
    """Marca um alerta preditivo como reconhecido."""
    alert = get_object_or_404(PredictiveAlert, pk=pk)
    alert.is_acknowledged = True
    alert.acknowledged_by = request.user
    alert.acknowledged_at = timezone.now()
    alert.save()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'ok': True})
    messages.success(request, 'Alerta reconhecido.')
    return redirect('predictive_ai:dashboard')


@login_required
def run_analysis_manual(request):
    """Execução manual da análise preditiva (Admin Master)."""
    if not request.user.is_admin_master:
        return JsonResponse({'error': 'Acesso negado'}, status=403)

    if request.method == 'POST':
        results = run_predictive_analysis()
        messages.success(
            request,
            f'Análise concluída! {results["companies_analyzed"]} empresas analisadas, '
            f'{results["alerts_created"]} alertas gerados.'
        )
        return redirect('predictive_ai:dashboard')
    return redirect('predictive_ai:dashboard')


@login_required
def suggestions_api(request):
    """API para obter sugestões baseadas em tipo e nível de risco."""
    tipo = request.GET.get('tipo_risco', '')
    nivel = request.GET.get('nivel_risco', 'MODERADO')

    suggestions = get_suggestions_for_risk(tipo, nivel)

    data = [{
        'titulo': s.titulo,
        'descricao': s.descricao,
        'categoria': s.get_categoria_display(),
        'norma': s.norma_referencia,
        'fundamentacao': s.fundamentacao,
    } for s in suggestions]

    return JsonResponse({'suggestions': data})


@login_required
def suggestion_list(request):
    """Lista de todas as sugestões NR cadastradas."""
    suggestions = NRSuggestion.objects.filter(is_active=True)

    tipo = request.GET.get('tipo')
    if tipo:
        suggestions = suggestions.filter(tipo_risco=tipo)

    return render(request, 'predictive_ai/suggestion_list.html', {
        'suggestions': suggestions,
        'risk_types': NRSuggestion.RISK_TYPE_CHOICES,
        'filter_tipo': tipo,
    })
