"""
Views para gestao de empresas.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse

from .models import Company, Announcement
from .forms import CompanySettingsForm, AnnouncementForm, CompanyAdminForm
from audit.models import AuditLog


def require_company_admin(view_func):
    """Decorator que verifica se o usuario e COMPANY_ADMIN."""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_company_admin:
            messages.error(request, 'Acesso restrito a administradores da empresa.')
            return redirect('accounts:dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


def require_admin_master(view_func):
    """Decorator que verifica se o usuario e ADMIN_MASTER."""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_admin_master:
            messages.error(request, 'Acesso restrito ao administrador master.')
            return redirect('accounts:dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


@login_required
@require_admin_master
def company_list(request):
    """Lista todas as empresas (apenas ADMIN_MASTER)."""
    status_filter = request.GET.get('status', '')
    search = request.GET.get('search', '')
    
    companies = Company.objects.all()
    if status_filter:
        companies = companies.filter(status=status_filter)
        
    if search:
        from django.db.models import Q
        companies = companies.filter(
            Q(nome_fantasia__icontains=search) | 
            Q(razao_social__icontains=search) | 
            Q(cnpj__icontains=search)
        )
    
    context = {
        'companies': companies,
        'status_filter': status_filter,
        'search': search,
    }
    return render(request, 'companies/company_list.html', context)


@login_required
@require_admin_master
def company_approve(request, pk):
    """Aprova uma empresa pendente."""
    company = get_object_or_404(Company, pk=pk)
    
    if company.status != 'PENDING':
        messages.warning(request, 'Esta empresa nao esta pendente de aprovacao.')
        return redirect('companies:list')
    
    company.approve(request.user)
    
    AuditLog.log(
        user=request.user,
        action='APPROVE',
        description=f'Empresa {company.nome_fantasia} aprovada',
        obj=company,
        request=request
    )
    
    messages.success(request, f'Empresa {company.nome_fantasia} aprovada com sucesso!')
    return redirect('companies:list')


@login_required
@require_admin_master
def company_reject(request, pk):
    """Rejeita uma empresa pendente."""
    company = get_object_or_404(Company, pk=pk)
    
    company.status = 'CANCELLED'
    company.save()
    
    AuditLog.log(
        user=request.user,
        action='REJECT',
        description=f'Empresa {company.nome_fantasia} rejeitada',
        obj=company,
        request=request
    )
    
    messages.success(request, f'Empresa {company.nome_fantasia} rejeitada.')
    return redirect('companies:list')


@login_required
@require_admin_master
def company_suspend(request, pk):
    """Suspende uma empresa."""
    company = get_object_or_404(Company, pk=pk)
    company.suspend()
    
    AuditLog.log(
        user=request.user,
        action='UPDATE',
        description=f'Empresa {company.nome_fantasia} suspensa',
        obj=company,
        request=request
    )
    
    messages.success(request, f'Empresa {company.nome_fantasia} suspensa.')
    return redirect('companies:list')


@login_required
@require_admin_master
def company_edit(request, pk):
    """Edita detalhes de faturamento e plano de uma empresa (apenas ADMIN_MASTER)."""
    company = get_object_or_404(Company, pk=pk)
    
    if request.method == 'POST':
        form = CompanyAdminForm(request.POST, instance=company)
        if form.is_valid():
            form.save()
            AuditLog.log(
                user=request.user,
                action='UPDATE',
                description=f'Dados de faturamento da empresa {company.nome_fantasia} atualizados',
                obj=company,
                request=request
            )
            messages.success(request, 'Dados da empresa atualizados com sucesso!')
            return redirect('companies:list')
    else:
        form = CompanyAdminForm(instance=company)
        
    return render(request, 'companies/company_edit.html', {
        'form': form,
        'company': company
    })


@login_required
@require_admin_master
def company_delete(request, pk):
    """Exclui permanentemente uma empresa e todos os seus dados vinculados."""
    company = get_object_or_404(Company, pk=pk)
    company_name = company.nome_fantasia
    
    # Audit log before deletion
    AuditLog.log(
        user=request.user,
        action='DELETE',
        description=f'Empresa {company_name} excluida permanentemente',
        obj=company,
        request=request
    )
    
    company.delete()
    
    messages.success(request, f'Empresa {company_name} e todos os seus dados foram removidos com sucesso.')
    return redirect('companies:list')


@login_required
@require_company_admin
def company_settings(request):
    """Configuracoes da empresa (logo, cores, dados)."""
    company = request.user.company
    
    if request.method == 'POST':
        form = CompanySettingsForm(request.POST, request.FILES, instance=company)
        if form.is_valid():
            form.save()
            
            AuditLog.log(
                user=request.user,
                action='UPDATE',
                description='Configuracoes da empresa atualizadas',
                obj=company,
                request=request
            )
            
            messages.success(request, 'Configuracoes salvas com sucesso!')
            return redirect('companies:settings')
    else:
        form = CompanySettingsForm(instance=company)
    
    return render(request, 'companies/settings.html', {'form': form, 'company': company})


@login_required
@require_company_admin
def announcement_list(request):
    """Lista comunicados da empresa."""
    company = request.user.company
    announcements = Announcement.objects.filter(company=company)
    
    return render(request, 'companies/announcement_list.html', {
        'announcements': announcements
    })


@login_required
@require_company_admin
def announcement_create(request):
    """Cria novo comunicado."""
    if request.method == 'POST':
        form = AnnouncementForm(request.POST)
        if form.is_valid():
            announcement = form.save(commit=False)
            announcement.company = request.user.company
            announcement.created_by = request.user
            announcement.save()
            
            messages.success(request, 'Comunicado criado com sucesso!')
            return redirect('companies:announcements')
    else:
        form = AnnouncementForm()
    
    return render(request, 'companies/announcement_form.html', {'form': form})


@login_required
@require_company_admin
def announcement_toggle(request, pk):
    """Ativa/desativa um comunicado."""
    announcement = get_object_or_404(
        Announcement,
        pk=pk,
        company=request.user.company
    )
    announcement.is_active = not announcement.is_active
    announcement.save()
    
    status = 'ativado' if announcement.is_active else 'desativado'
    messages.success(request, f'Comunicado {status}.')
    return redirect('companies:announcements')
