"""
Views para autenticacao e dashboards de usuarios.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib import messages
from django.views.generic import CreateView, TemplateView
from django.urls import reverse_lazy
from django.db.models import Count, Avg

from .forms import LoginForm, CompanySignupForm, TermsAcceptanceForm
from .models import User
from companies.models import Company
from employees.models import Employee
from forms_builder.models import FormInstance, FormAssignment, FormAnswer
from audit.models import AuditLog


class CustomLoginView(LoginView):
    """View de login customizada."""
    
    form_class = LoginForm
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True
    
    def form_valid(self, form):
        user = form.get_user()
        
        if user.company and user.company.status == 'PENDING':
            messages.warning(self.request, 'Sua empresa ainda esta aguardando aprovacao.')
            return redirect('accounts:pending_approval')
        
        if user.company and user.company.status == 'SUSPENDED':
            messages.error(self.request, 'Sua empresa esta suspensa. Entre em contato com o suporte.')
            return redirect('accounts:login')
        
        AuditLog.log(
            user=user,
            action='LOGIN',
            description=f'Usuario {user.email} realizou login',
            request=self.request
        )
        
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('accounts:dashboard')


class CustomLogoutView(LogoutView):
    """View de logout customizada."""
    
    def dispatch(self, request, *args, **kwargs):
        url = '/'
        if request.user.is_authenticated:
            user = request.user
            AuditLog.log(
                user=user,
                action='LOGOUT',
                description=f'Usuario {user.email} realizou logout',
                request=request
            )
            
            if user.role == 'ADMIN_MASTER':
                url = '/'
            elif getattr(user, 'company', None):
                website = user.company.configs.get('website') if getattr(user.company, 'configs', None) else None
                if website and website.startswith('http'):
                    url = website
            
            logout(request)
        return redirect(url)


class CompanySignupView(CreateView):
    """View para cadastro de nova empresa."""
    
    form_class = CompanySignupForm
    template_name = 'accounts/company_signup.html'
    success_url = reverse_lazy('accounts:pending_approval')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            'Cadastro realizado com sucesso! Aguarde a aprovacao da sua empresa.'
        )
        return response


class PendingApprovalView(TemplateView):
    """View para exibir mensagem de aguardando aprovacao."""
    
    template_name = 'accounts/pending_approval.html'


@login_required
def dashboard(request):
    """Dashboard principal - redireciona baseado no role do usuario."""
    user = request.user
    
    if user.is_admin_master:
        return redirect('accounts:admin_master_dashboard')
    elif user.is_company_admin:
        return redirect('accounts:company_admin_dashboard')
    else:
        return redirect('accounts:employee_dashboard')


@login_required
def admin_master_dashboard(request):
    """Dashboard do ADMIN_MASTER."""
    if not request.user.is_admin_master:
        messages.error(request, 'Acesso nao autorizado.')
        return redirect('accounts:dashboard')
    
    context = {
        'pending_companies': Company.objects.filter(status='PENDING').count(),
        'active_companies': Company.objects.filter(status='ACTIVE').count(),
        'total_users': User.objects.count(),
        'recent_companies': Company.objects.order_by('-created_at')[:10],
        'recent_logs': AuditLog.objects.select_related('user', 'company').order_by('-created_at')[:20],
    }
    
    return render(request, 'accounts/admin_master_dashboard.html', context)


@login_required
def company_admin_dashboard(request):
    """Dashboard do COMPANY_ADMIN."""
    if not request.user.is_company_admin:
        messages.error(request, 'Acesso nao autorizado.')
        return redirect('accounts:dashboard')
    
    company = request.user.company
    
    active_forms = FormInstance.objects.filter(
        company=company,
        status='ACTIVE'
    ).select_related('template')
    
    form_stats = []
    for form in active_forms:
        stats = {
            'form': form,
            'total': form.assignments.count(),
            'completed': form.assignments.filter(status='COMPLETED').count(),
            'response_rate': form.get_response_rate(),
            'avg_score': form.get_average_score()
        }
        form_stats.append(stats)
    
    context = {
        'company': company,
        'total_employees': company.get_employee_count(),
        'active_forms_count': company.get_active_forms_count(),
        'form_stats': form_stats,
        'recent_employees': Employee.objects.filter(company=company).order_by('-created_at')[:5],
        'announcements': company.announcements.filter(is_active=True)[:5],
    }
    
    return render(request, 'accounts/company_admin_dashboard.html', context)


@login_required
def admin_laudos(request):
    """View para o Admin Master gerenciar e gerar Laudos Individuais com IA."""
    if request.user.role != 'ADMIN_MASTER':
        messages.error(request, 'Acesso restrito.')
        return redirect('accounts:dashboard')
        
    # Busca funconarios/assignments que finalizaram o form
    from forms_builder.models import FormAssignment
    
    # Todos concluidos, ordendo por mais recentes
    completed_assignments = FormAssignment.objects.filter(
        status='COMPLETED'
    ).select_related(
        'employee', 'employee__company', 'form_instance', 'diagnostic'
    ).order_by('-completed_at')
    
    return render(request, 'accounts/admin_laudos.html', {
        'assignments': completed_assignments
    })

@login_required
def generate_laudo_action(request, assignment_id):
    """View acionada pelo botao verde para gerar o laudo via Groq."""
    if request.user.role != 'ADMIN_MASTER':
        messages.error(request, 'Acesso restrito.')
        return redirect('accounts:dashboard')
        
    from forms_builder.models import FormAssignment
    from ai_analysis.engine import generate_employee_diagnostic
    
    assignment = get_object_or_404(FormAssignment, pk=assignment_id)
    
    if assignment.status != 'COMPLETED':
        messages.warning(request, 'Funcionario ainda nao concluiu o questionario.')
        return redirect('accounts:admin_laudos')
        
    # Gera ou retorna o existente
    result = generate_employee_diagnostic(assignment)
    
    if isinstance(result, dict) and result.get('status') == 'failed':
        messages.error(request, f"Erro na IA: {result.get('error')}")
    else:
        messages.success(request, f"Laudo de {assignment.employee.nome} gerado com sucesso!")
        
    from audit.models import AuditLog
    AuditLog.log(
        user=request.user,
        action='EXPORT',
        description=f'Gerou (ou acessou) Laudo IA para {assignment.employee.nome}',
        obj=assignment,
        request=request
    )
    
    return redirect('accounts:admin_laudos')

@login_required
def employee_dashboard(request):
    """Dashboard do EMPLOYEE."""
    user = request.user
    
    try:
        employee = user.employee_profile
    except Employee.DoesNotExist:
        employee = Employee.objects.filter(email=user.email, company=user.company).first()
        if employee:
            employee.user = user
            employee.save()
    
    if not employee:
        messages.warning(request, 'Seu perfil de funcionario nao foi encontrado.')
        return render(request, 'accounts/employee_dashboard.html', {'employee': None})
    
    # Auto-atribuicao de formularios ativos que o funcionario ainda nao recebeu
    if employee.company:
        from forms_builder.models import FormInstance, FormAssignment
        active_instances = FormInstance.objects.filter(
            company=employee.company,
            status='ACTIVE'
        )
        for instance in active_instances:
            if instance.is_active: # Valida datas tb
                FormAssignment.objects.get_or_create(
                    employee=employee,
                    form_instance=instance,
                    defaults={'status': 'PENDING'}
                )
    
    pending_forms = employee.get_pending_forms()
    completed_forms = employee.get_completed_forms()
    
    announcements = []
    if employee.company:
        announcements = employee.company.announcements.filter(is_active=True)[:5]
    
    context = {
        'employee': employee,
        'pending_forms': pending_forms,
        'completed_forms': completed_forms,
        'announcements': announcements,
    }
    
    return render(request, 'accounts/employee_dashboard.html', context)


@login_required
def accept_terms(request):
    """View para aceite de termos e politica de privacidade."""
    if request.user.terms_accepted and request.user.privacy_accepted:
        return redirect('accounts:dashboard')
    
    if request.method == 'POST':
        form = TermsAcceptanceForm(request.POST)
        if form.is_valid():
            request.user.accept_terms()
            request.user.accept_privacy()
            messages.success(request, 'Termos aceitos com sucesso!')
            return redirect('accounts:dashboard')
    else:
        form = TermsAcceptanceForm()
    
    return render(request, 'accounts/accept_terms.html', {'form': form})


@login_required
def profile_update(request):
    """Permite que o usuário (especialmente psicólogos) atualize seu CRP e assinatura."""
    user = request.user
    
    if request.method == 'POST':
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.professional_crp = request.POST.get('professional_crp', user.professional_crp)
        
        if 'signature_image' in request.FILES:
            user.signature_image = request.FILES['signature_image']
            
        user.save()
        messages.success(request, 'Perfil atualizado com sucesso!')
        return redirect('accounts:dashboard')
        
    return render(request, 'accounts/profile_update.html', {
        'user': user
    })
