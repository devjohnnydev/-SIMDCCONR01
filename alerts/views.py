"""Views para Alertas Inteligentes."""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse

from .models import Alert
from .services import run_all_checks


@login_required
def alert_list(request):
    """Lista de alertas do sistema."""
    company = None
    if request.user.is_admin_master:
        company_id = request.GET.get('company')
        if company_id:
            from companies.models import Company
            company = Company.objects.filter(pk=company_id).first()
        
        if company:
            alerts = Alert.objects.filter(company=company)
        else:
            alerts = Alert.objects.all()
    elif request.user.company:
        alerts = Alert.objects.filter(company=request.user.company)
    else:
        alerts = Alert.objects.none()

    # Filtros
    severity = request.GET.get('severity')
    tipo = request.GET.get('tipo')
    unread_only = request.GET.get('unread')

    if severity:
        alerts = alerts.filter(severidade=severity)
    if tipo:
        alerts = alerts.filter(tipo=tipo)
    if unread_only:
        alerts = alerts.filter(is_read=False)

    alerts = alerts.order_by('-created_at')[:100]

    unread_count = Alert.unread_count_for_user(request.user)
    
    companies_list = None
    if request.user.is_admin_master:
        from companies.models import Company
        companies_list = Company.objects.filter(status='ACTIVE')

    return render(request, 'alerts/alert_list.html', {
        'alerts': alerts,
        'unread_count': unread_count,
        'filter_severity': severity,
        'filter_tipo': tipo,
        'filter_unread': unread_only,
        'type_choices': Alert.TYPE_CHOICES,
        'severity_choices': Alert.SEVERITY_CHOICES,
        'companies_list': companies_list,
        'company': company,
    })


@login_required
def mark_read(request, pk):
    """Marca um alerta como lido."""
    alert = get_object_or_404(Alert, pk=pk)
    alert.mark_read()
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'ok': True})
    return redirect('alerts:list')


@login_required
def mark_resolved(request, pk):
    """Marca um alerta como resolvido."""
    alert = get_object_or_404(Alert, pk=pk)
    alert.mark_resolved()
    messages.success(request, 'Alerta marcado como resolvido.')
    return redirect('alerts:list')


@login_required
def mark_all_read(request):
    """Marca todos os alertas como lidos."""
    if request.method == 'POST':
        if request.user.is_admin_master:
            Alert.objects.filter(is_read=False).update(is_read=True)
        elif request.user.company:
            Alert.objects.filter(
                company=request.user.company, is_read=False
            ).update(is_read=True)
        messages.success(request, 'Todos os alertas marcados como lidos.')
    return redirect('alerts:list')


@login_required
def unread_count_api(request):
    """API para badge de notificação (count de alertas não lidos)."""
    count = Alert.unread_count_for_user(request.user)
    return JsonResponse({'count': count})


@login_required
def run_checks_manual(request):
    """Execução manual de todas as verificações de alertas (Admin Master)."""
    if not request.user.is_admin_master:
        return JsonResponse({'error': 'Acesso negado'}, status=403)

    if request.method == 'POST':
        results = run_all_checks()
        messages.success(
            request,
            f'Verificação concluída! {results["total_created"]} alertas criados.'
        )
        return redirect('alerts:list')
    return redirect('alerts:list')
