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
        
    from forms_builder.models import FormAssignment
    from accounts.models import User
    from reports.models import SignerProfile
    
    try:
        completed_assignments = FormAssignment.objects.filter(
            status='COMPLETED'
        ).select_related(
            'employee', 'employee__company', 'form_instance'
        ).order_by('-completed_at')
        
        professionals = User.objects.filter(role='ADMIN_MASTER')
        signatarios = SignerProfile.objects.filter(is_active=True)
        
        return render(request, 'accounts/admin_laudos.html', {
            'assignments': completed_assignments,
            'professionals': professionals,
            'signatarios': signatarios,
        })
    except Exception as e:
        messages.error(request, f'Erro ao carregar laudos: {str(e)}')
        return render(request, 'accounts/admin_laudos.html', {
            'assignments': [],
            'professionals': [],
            'signatarios': [],
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

# --- NOVAS ROTAS PARA ASSINATURA ELETRONICA ---

@login_required
def sign_laudo_internal(request, diagnostic_id):
    """Assinatura de laudo individual pela interface (Assinatura do Profissional)"""
    from reports.models import EmployeeDiagnostic, SignerProfile
    from django.utils import timezone
    
    diagnostic = get_object_or_404(EmployeeDiagnostic, pk=diagnostic_id)
    
    if request.method == 'POST':
        if request.user.role not in ['ADMIN_MASTER', 'COMPANY_ADMIN']:
            messages.error(request, 'Ação não permitida. Apenas Peritos e Administradores podem assinar.')
            return redirect('accounts:admin_laudos')
        
        signer_profile_id = request.POST.get('signer_profile_id')
        if signer_profile_id:
            try:
                signer = SignerProfile.objects.get(pk=signer_profile_id)
                diagnostic.signer_profile = signer
            except SignerProfile.DoesNotExist:
                pass

        diagnostic.is_signed = True
        diagnostic.signed_by = request.user
        diagnostic.signature_method = 'INTERNAL'
        diagnostic.signature_timestamp = timezone.now()
        diagnostic.save()
        
        messages.success(request, 'Laudo assinado eletronicamente com sucesso.')
        
    return redirect('reports:view_diagnostic', validation_code=diagnostic.validation_code)


@login_required
def sign_laudo_govbr(request, diagnostic_id):
    """Simulação de assinatura via API do Gov.br"""
    from reports.models import EmployeeDiagnostic, SignerProfile
    from django.utils import timezone
    import uuid
    
    diagnostic = get_object_or_404(EmployeeDiagnostic, pk=diagnostic_id)
    
    if request.method == 'POST':
        if request.user.role not in ['ADMIN_MASTER', 'COMPANY_ADMIN']:
            messages.error(request, 'Ação não permitida. Faça login com conta habilitada.')
            return redirect('accounts:admin_laudos')
        
        signer_profile_id = request.POST.get('signer_profile_id')
        if signer_profile_id:
            try:
                signer = SignerProfile.objects.get(pk=signer_profile_id)
                diagnostic.signer_profile = signer
            except SignerProfile.DoesNotExist:
                pass

        diagnostic.is_signed = True
        diagnostic.signed_by = request.user
        diagnostic.signature_method = 'GOVBR'
        diagnostic.signature_timestamp = timezone.now()
        diagnostic.govbr_token = f"GOVBR-{uuid.uuid4().hex[:12].upper()}"
        diagnostic.save()
        
        messages.success(request, 'Sucesso! O laudo foi validado digitalmente com selo Gov.br.')
        
    return redirect('reports:view_diagnostic', validation_code=diagnostic.validation_code)


@login_required
def assign_signatory(request):
    """Atribui um signatário específico a um laudo."""
    if request.user.role != 'ADMIN_MASTER':
        messages.error(request, 'Ação não permitida.')
        return redirect('accounts:dashboard')
        
    if request.method == 'POST':
        from reports.models import EmployeeDiagnostic
        from accounts.models import User
        
        diagnostic_id = request.POST.get('diagnostic_id')
        professional_id = request.POST.get('professional_id')
        
        diagnostic = get_object_or_404(EmployeeDiagnostic, pk=diagnostic_id)
        professional = get_object_or_404(User, pk=professional_id)
        
        diagnostic.assigned_professional = professional
        diagnostic.save()
        
        messages.success(request, f'Profissional {professional.get_full_name()} atribuído como signatário do laudo.')
        
    return redirect('accounts:admin_laudos')


@login_required
def bulk_sign_laudos(request):
    """Assinatura em lote selecionado no painel Admin"""
    from reports.models import EmployeeDiagnostic, SignerProfile
    from django.utils import timezone
    
    if request.method == 'POST':
        if request.user.role not in ['ADMIN_MASTER', 'COMPANY_ADMIN']:
            messages.error(request, 'Ação não permitida para o seu perfil.')
            return redirect('accounts:dashboard')
            
        diagnostic_ids = request.POST.getlist('diagnostic_ids')
        signer_profile_id = request.POST.get('signer_profile_id')
        signature_method = request.POST.get('signature_method', 'INTERNAL')
        
        if not diagnostic_ids:
            messages.warning(request, 'Nenhum laudo foi selecionado para assinatura.')
            return redirect('accounts:admin_laudos')
        
        signer = None
        if signer_profile_id:
            try:
                signer = SignerProfile.objects.get(pk=signer_profile_id)
            except SignerProfile.DoesNotExist:
                pass
            
        diagnostics = EmployeeDiagnostic.objects.filter(id__in=diagnostic_ids, is_signed=False)
        count = diagnostics.count()
        
        for d in diagnostics:
            d.is_signed = True
            if d.assigned_professional:
                d.signed_by = d.assigned_professional
            else:
                d.signed_by = request.user
            
            if signer:
                d.signer_profile = signer
                
            d.signature_method = signature_method
            d.signature_timestamp = timezone.now()
            
            if signature_method == 'GOVBR':
                import uuid
                d.govbr_token = f"GOVBR-{uuid.uuid4().hex[:12].upper()}"
            
            d.save()
            
        messages.success(request, f'{count} laudo(s) assinados em lote com as rubricas correspondentes.')
        
    return redirect('accounts:admin_laudos')


@login_required
def manage_signatarios(request):
    """CRUD de perfis de signatários."""
    from reports.models import SignerProfile
    
    if request.user.role != 'ADMIN_MASTER':
        messages.error(request, 'Acesso restrito.')
        return redirect('accounts:dashboard')
    
    if request.method == 'POST':
        nome = request.POST.get('nome_completo', '').strip()
        if not nome:
            messages.error(request, 'O nome do signatário é obrigatório.')
            return redirect('accounts:manage_signatarios')
        
        signer = SignerProfile(
            nome_completo=nome,
            registro_profissional=request.POST.get('registro_profissional', '').strip(),
            especialidade=request.POST.get('especialidade', 'PSICOLOGO'),
            email=request.POST.get('email', '').strip(),
            govbr_cpf=request.POST.get('govbr_cpf', '').strip(),
        )
        if 'signature_image' in request.FILES:
            signer.signature_image = request.FILES['signature_image']
        signer.save()
        messages.success(request, f'Signatário "{nome}" cadastrado com sucesso!')
        return redirect('accounts:manage_signatarios')
    
    signatarios = SignerProfile.objects.all()
    return render(request, 'accounts/manage_signatarios.html', {
        'signatarios': signatarios,
        'specialty_choices': SignerProfile.SPECIALTY_CHOICES,
    })


@login_required
def delete_signatario(request, pk):
    """Remove um signatário."""
    from reports.models import SignerProfile
    
    if request.user.role != 'ADMIN_MASTER':
        messages.error(request, 'Acesso restrito.')
        return redirect('accounts:dashboard')
    
    signer = get_object_or_404(SignerProfile, pk=pk)
    if request.method == 'POST':
        nome = signer.nome_completo
        signer.delete()
        messages.success(request, f'Signatário "{nome}" removido.')
    return redirect('accounts:manage_signatarios')


@login_required
def edit_signatario(request, pk):
    """Edita dados de um signatário existente."""
    from reports.models import SignerProfile
    
    if request.user.role != 'ADMIN_MASTER':
        messages.error(request, 'Acesso restrito.')
        return redirect('accounts:dashboard')
    
    signer = get_object_or_404(SignerProfile, pk=pk)
    
    if request.method == 'POST':
        signer.nome_completo = request.POST.get('nome_completo', signer.nome_completo).strip()
        signer.registro_profissional = request.POST.get('registro_profissional', signer.registro_profissional).strip()
        signer.especialidade = request.POST.get('especialidade', signer.especialidade)
        signer.email = request.POST.get('email', signer.email).strip()
        signer.govbr_cpf = request.POST.get('govbr_cpf', signer.govbr_cpf).strip()
        if 'signature_image' in request.FILES:
            signer.signature_image = request.FILES['signature_image']
        signer.save()
        messages.success(request, f'Signatário "{signer.nome_completo}" atualizado com sucesso!')
        return redirect('accounts:manage_signatarios')
    
    return render(request, 'accounts/edit_signatario.html', {
        'signer': signer,
        'specialty_choices': SignerProfile.SPECIALTY_CHOICES,
    })


@login_required
def department_reports_list(request):
    """Listagem de laudos por departamento para a empresa."""
    if request.user.role != 'COMPANY_ADMIN':
        messages.error(request, 'Acesso restrito a administradores de empresa.')
        return redirect('accounts:dashboard')
    
    from reports.models import DepartmentDiagnostic
    from employees.models import Employee
    from forms_builder.models import FormInstance
    
    company = request.user.company
    
    # Busca todos os setores que têm pelo menos 1 funcionário ativo
    setores = Employee.objects.filter(company=company, status='ACTIVE').values_list('setor', flat=True).distinct()
    
    # Busca formulários ativos para esta empresa (excluindo rascunhos)
    active_forms = FormInstance.objects.filter(company=company).exclude(status='DRAFT')
    
    # Laudos já gerados
    existing_reports = DepartmentDiagnostic.objects.filter(company=company).select_related('form_instance')
    
    return render(request, 'accounts/department_reports_list.html', {
        'setores': setores,
        'active_forms': active_forms,
        'reports': existing_reports
    })


@login_required
def generate_department_report_action(request):
    """Action POST para gerar laudo de departamento via IA."""
    if request.user.role != 'COMPANY_ADMIN':
        messages.error(request, 'Ação não permitida.')
        return redirect('accounts:dashboard')
        
    if request.method == 'POST':
        from forms_builder.models import FormInstance
        from ai_analysis.engine import generate_department_diagnostic
        
        setor = request.POST.get('setor')
        form_id = request.POST.get('form_id')
        
        form_instance = get_object_or_404(FormInstance, pk=form_id, company=request.user.company)
        
        result = generate_department_diagnostic(request.user.company, setor, form_instance, user=request.user)
        
        if isinstance(result, dict) and 'error' in result:
            messages.error(request, result['error'])
        else:
            messages.success(request, f'Laudo do departamento "{setor}" gerado com sucesso!')
            
    return redirect('accounts:department_reports_list')


@login_required
def view_department_report(request, setor, form_id):
    """Visualização de um laudo de departamento específico."""
    from reports.models import DepartmentDiagnostic
    
    report = get_object_or_404(
        DepartmentDiagnostic, 
        company=request.user.company, 
        setor=setor, 
        form_instance_id=form_id
    )
    
    if request.user.role not in ['ADMIN_MASTER', 'COMPANY_ADMIN']:
        messages.error(request, 'Acesso negado.')
        return redirect('accounts:dashboard')
        
    return render(request, 'reports/department_diagnostic_view.html', {
        'report': report,
        'data': report.diagnostic_data
    })


def test_resend(request):
    """View de diagnostico para o Resend API."""
    from django.conf import settings
    from django.http import HttpResponse
    import json
    import urllib.request
    
    api_key = getattr(settings, 'RESEND_API_KEY', 'NAO DEFINIDA')
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'NAO DEFINIDO')
    
    # Mascarar chave
    masked_key = f"{api_key[:6]}...{api_key[-4:]}" if len(api_key) > 10 else "CHAVE MUITO CURTA OU NULA"
    
    payload = {
        "from": from_email,
        "to": ["bragabraga19888@gmail.com"],
        "subject": "Teste Direto Resend API",
        "html": "<h1>Funciona!</h1><p>Se voce esta lendo isso, a API do Resend respondeu com sucesso.</p>"
    }
    
    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request("https://api.resend.com/emails", data=data)
        req.add_header('Content-Type', 'application/json')
        req.add_header('Authorization', f'Bearer {api_key}')
        req.add_header('User-Agent', 'SafeClima-SaaS/1.0')
        
        with urllib.request.urlopen(req) as response:
            res_body = response.read().decode('utf-8')
            return HttpResponse(
                f"<h1>SUCESSO NA API</h1>"
                f"<p>O Resend aceitou o e-mail.</p>"
                f"<p><b>Configus usadas:</b><br>Key: {masked_key}<br>From: {from_email}</p>"
                f"<pre>{res_body}</pre>"
            )
    except urllib.error.HTTPError as e:
        res_body = e.read().decode('utf-8')
        return HttpResponse(
            f"<h1>ERRO NA API RESEND (HTTP {e.code})</h1>"
            f"<p>O Resend recusou o e-mail.</p>"
            f"<p><b>Configus usadas:</b><br>Key: {masked_key}<br>From: {from_email}</p>"
            f"<h3>Resposta do Resend:</h3>"
            f"<pre style='background:#f4f4f4; padding:10px; border:1px solid #ccc;'>{res_body}</pre>"
        )
    except Exception as e:
        return HttpResponse(f"<h1>ERRO GENERICO</h1><pre>{str(e)}</pre>")
