"""
Views para gestao de funcionarios.
"""
import csv
import io
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.core.paginator import Paginator
from datetime import datetime

from .models import Employee, EmployeeImportLog
from .forms import EmployeeForm, EmployeeImportForm
from companies.views import require_company_admin
from audit.models import AuditLog


@login_required
@require_company_admin
def employee_list(request):
    """Lista funcionarios da empresa."""
    company = request.user.company
    
    employees = Employee.objects.filter(company=company)
    
    search = request.GET.get('search', '')
    if search:
        employees = employees.filter(nome__icontains=search)
    
    setor = request.GET.get('setor', '')
    if setor:
        employees = employees.filter(setor=setor)
    
    status = request.GET.get('status', '')
    if status:
        employees = employees.filter(status=status)
    
    setores = Employee.objects.filter(company=company).values_list('setor', flat=True).distinct()
    
    paginator = Paginator(employees, 20)
    page = request.GET.get('page', 1)
    employees = paginator.get_page(page)
    
    context = {
        'employees': employees,
        'setores': setores,
        'search': search,
        'setor_filter': setor,
        'status_filter': status,
    }
    return render(request, 'employees/employee_list.html', context)


@login_required
@require_company_admin
def employee_create(request):
    """Cria novo funcionario."""
    company = request.user.company
    
    if not company.can_add_employee():
        messages.error(request, 'Limite de funcionarios do plano atingido.')
        return redirect('employees:list')
    
    if request.method == 'POST':
        form = EmployeeForm(request.POST, company=company)
        if form.is_valid():
            employee = form.save(commit=False)
            employee.company = company
            employee.save()
            
            AuditLog.log(
                user=request.user,
                action='CREATE',
                description=f'Funcionario {employee.nome} criado',
                obj=employee,
                request=request
            )
            
            messages.success(request, f'Funcionario {employee.nome} criado com sucesso!')
            return redirect('employees:list')
    else:
        form = EmployeeForm(company=company)
    
    return render(request, 'employees/employee_form.html', {'form': form, 'action': 'Novo'})


@login_required
@require_company_admin
def employee_edit(request, pk):
    """Edita funcionario existente."""
    company = request.user.company
    employee = get_object_or_404(Employee, pk=pk, company=company)
    
    if request.method == 'POST':
        form = EmployeeForm(request.POST, instance=employee, company=company)
        if form.is_valid():
            form.save()
            
            AuditLog.log(
                user=request.user,
                action='UPDATE',
                description=f'Funcionario {employee.nome} atualizado',
                obj=employee,
                request=request
            )
            
            messages.success(request, f'Funcionario {employee.nome} atualizado!')
            return redirect('employees:list')
    else:
        form = EmployeeForm(instance=employee, company=company)
    
    return render(request, 'employees/employee_form.html', {
        'form': form,
        'action': 'Editar',
        'employee': employee
    })


@login_required
@require_company_admin
def employee_deactivate(request, pk):
    """Desativa um funcionario."""
    company = request.user.company
    employee = get_object_or_404(Employee, pk=pk, company=company)
    
    employee.deactivate()
    
    AuditLog.log(
        user=request.user,
        action='UPDATE',
        description=f'Funcionario {employee.nome} desativado',
        obj=employee,
        request=request
    )
    
    messages.success(request, f'Funcionario {employee.nome} desativado.')
    return redirect('employees:list')


@login_required
@require_company_admin
def employee_import(request):
    """Importa funcionarios via CSV."""
    company = request.user.company
    
    if request.method == 'POST':
        form = EmployeeImportForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES['file']
            
            import_log = EmployeeImportLog.objects.create(
                company=company,
                file_name=csv_file.name,
                status='PROCESSING',
                created_by=request.user
            )
            
            try:
                decoded_file = csv_file.read().decode('utf-8-sig')
                io_string = io.StringIO(decoded_file)
                reader = csv.DictReader(io_string, delimiter=';')
                
                success_count = 0
                error_count = 0
                errors = []
                total_rows = 0
                
                for row_num, row in enumerate(reader, start=2):
                    total_rows += 1
                    try:
                        # Helper to get value from multiple possible keys (Portuguese/Internal)
                        def get_val(keys):
                            for k in keys:
                                if row.get(k): return row[k].strip()
                            return ''

                        nome = get_val(['Nome Completo', 'nome'])
                        email = get_val(['e-mail corporativo', 'email']).lower()
                        cpf = get_val(['CPF', 'cpf'])
                        cpf = ''.join(filter(str.isdigit, cpf))
                        setor = get_val(['Departamento', 'setor'])
                        cargo = get_val(['Cargo/função', 'cargo'])
                        centro_de_custo = get_val(['Centro de Custo', 'centro_de_custo'])
                        matricula = get_val(['Matricula', 'matricula', 'MATRICULA'])
                        
                        raw_admissao = get_val(['data de admissão', 'data_admissao'])
                        raw_nascimento = get_val(['data de nascimento', 'data_nascimento'])
                        raw_demissao = get_val(['data de demissão', 'data_demissao'])
                        
                        def parse_date(date_str):
                            if not date_str: return None
                            for fmt in ('%d/%m/%Y', '%Y-%m-%d'):
                                try:
                                    return datetime.strptime(date_str, fmt).date()
                                except ValueError:
                                    continue
                            return None

                        data_admissao = parse_date(raw_admissao) or datetime.now().date()
                        data_nascimento = parse_date(raw_nascimento)
                        data_demissao = parse_date(raw_demissao)
                        
                        # Superior Imediato (lookup by email or name if possible)
                        gestor_val = get_val(['Superior Imediato', 'gestor'])
                        gestor = None
                        if gestor_val:
                            # Try email first, then name
                            gestor = Employee.objects.filter(company=company, email__iexact=gestor_val).first()
                            if not gestor:
                                gestor = Employee.objects.filter(company=company, nome__icontains=gestor_val).first()

                        status_val = get_val(['Status', 'status']).upper()
                        status = 'ACTIVE'
                        if 'INATIVO' in status_val or 'OFF' in status_val or 'TERMINATED' in status_val:
                            status = 'TERMINATED'

                        employee, created = Employee.objects.update_or_create(
                            company=company,
                            email=email,
                            defaults={
                                'nome': nome,
                                'cpf': cpf,
                                'setor': setor,
                                'cargo': cargo,
                                'centro_de_custo': centro_de_custo,
                                'turno': row.get('turno', 'FULL').strip().upper(),
                                'data_admissao': data_admissao,
                                'data_nascimento': data_nascimento,
                                'data_demissao': data_demissao,
                                'matricula': matricula,
                                'gestor': gestor,
                                'status': status
                            }
                        )
                        success_count += 1
                        
                    except Exception as e:
                        error_count += 1
                        errors.append({
                            'row': row_num,
                            'data': dict(row),
                            'error': str(e)
                        })
                
                import_log.total_rows = total_rows
                import_log.success_count = success_count
                import_log.error_count = error_count
                import_log.errors = errors
                import_log.status = 'COMPLETED' if error_count == 0 else 'COMPLETED'
                import_log.save()
                
                AuditLog.log(
                    user=request.user,
                    action='IMPORT',
                    description=f'Importacao de {success_count} funcionarios via CSV',
                    obj=import_log,
                    request=request
                )
                
                messages.success(
                    request,
                    f'Importacao concluida: {success_count} importados, {error_count} erros.'
                )
                
            except Exception as e:
                import_log.status = 'FAILED'
                import_log.errors = [{'error': str(e)}]
                import_log.save()
                messages.error(request, f'Erro na importacao: {str(e)}')
            
            return redirect('employees:list')
    else:
        form = EmployeeImportForm()
    
    return render(request, 'employees/employee_import.html', {'form': form})


@login_required
@require_company_admin
def employee_export_template(request):
    """Exporta template CSV para importacao."""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="template_funcionarios.csv"'
    response.write('\ufeff')
    
    writer = csv.writer(response, delimiter=';')
    writer.writerow([
        'Nome Completo', 'e-mail corporativo', 'CPF', 'Departamento', 'Cargo/função',
        'Centro de Custo', 'Superior Imediato', 'data de nascimento', 'data de admissão', 'matricula', 'turno'
    ])
    writer.writerow([
        'Joao da Silva', 'joao@empresa.com', '12345678901', 'TI', 'Analista',
        'CC-001', 'gestor@empresa.com', '15/05/1985', '01/01/2024', '001', 'FULL'
    ])
    
    return response


@login_required
@require_company_admin
def employee_create_user(request, pk):
    """Cria conta de usuario para funcionario."""
    company = request.user.company
    employee = get_object_or_404(Employee, pk=pk, company=company)
    
    if employee.user:
        messages.warning(request, 'Este funcionario ja possui uma conta de usuario.')
        return redirect('employees:list')
    
    user = employee.create_user_account()
    
    AuditLog.log(
        user=request.user,
        action='CREATE',
        description=f'Conta de usuario criada para {employee.nome}',
        obj=user,
        request=request
    )
    
    messages.success(
        request,
        f'Conta criada para {employee.nome}. A senha de acesso padrao é o CPF do funcionario (apenas numeros).'
    )
    return redirect('employees:list')
