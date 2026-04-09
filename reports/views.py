"""
Views para geracao de relatorios e dashboards.
"""
import io
import base64
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.db.models import Avg, Count, Q
from django.utils import timezone

# WeasyPrint importado de forma lazily dentro de cada view para evitar
# falha na inicializacao do Django quando bibliotecas do sistema nao estao presentes.

from .models import Report, EmployeeDiagnostic
from .utils_charts import generate_pie_chart_svg
from forms_builder.models import FormInstance, FormAnswer, FormQuestion, FormAssignment
from companies.views import require_company_admin, require_admin_master
from audit.models import AuditLog


@login_required
@require_company_admin
def report_list(request):
    """Lista relatorios gerados."""
    company = request.user.company
    reports = Report.objects.filter(company=company)
    
    return render(request, 'reports/report_list.html', {'reports': reports})


def get_dashboard_data(company):
    """Helper function to fetch dashboard metrics for a company."""
    # Inclui Ativos e Encerrados para que possam ver métricas de pesquisas finalizadas
    active_forms = FormInstance.objects.filter(
        company=company, 
        status__in=['ACTIVE', 'CLOSED']
    ).order_by('-created_at')
    
    total_employees = company.get_employee_count()
    active_forms_count = active_forms.filter(status='ACTIVE').count()
    
    form_metrics = []
    for form in active_forms:
        total = form.assignments.count()
        completed_assignments = form.assignments.filter(status='COMPLETED').select_related('employee')
        pending_assignments = form.assignments.filter(status__in=['PENDING', 'IN_PROGRESS']).select_related('employee')
        
        completed_count = completed_assignments.count()
        rate = round((completed_count / total * 100), 1) if total > 0 else 0
        
        avg_score = FormAnswer.objects.filter(
            assignment__form_instance=form,
            question__question_type__in=['SCALE', 'SCALE_10']
        ).aggregate(avg=Avg('numeric_value'))['avg']
        
        # Dados de Departamentos (Ranking)
        dept_scores = list(form.get_department_scores())
        worst_dept = dept_scores[0] if dept_scores else None
        
        # Listas de nomes (respeitando anonimato se houver restrição futura, mas no momento permitindo)
        responded_list = [a.employee.nome for a in completed_assignments]
        pending_list = [a.employee.nome for a in pending_assignments]
        
        form_metrics.append({
            'form': form,
            'total': total,
            'completed': completed_count,
            'response_rate': rate,
            'avg_score': round(avg_score, 2) if avg_score else None,
            'dept_scores': dept_scores,
            'worst_dept': worst_dept,
            'responded_list': responded_list,
            'pending_list': pending_list,
        })
    
    climate_score = FormAnswer.objects.filter(
        assignment__form_instance__company=company,
        assignment__form_instance__template__category='CLIMATE',
        question__question_type__in=['SCALE', 'SCALE_10']
    ).aggregate(avg=Avg('numeric_value'))['avg']
    
    wellbeing_score = FormAnswer.objects.filter(
        assignment__form_instance__company=company,
        assignment__form_instance__template__category='WELLBEING',
        question__question_type__in=['SCALE', 'SCALE_10']
    ).aggregate(avg=Avg('numeric_value'))['avg']
    
    from employees.models import Employee
    # Funcionários por Setor
    sector_data = Employee.objects.filter(
        company=company,
        status='ACTIVE'
    ).values('setor').annotate(count=Count('id')).order_by('-count')
    
    # Funcionários por Centro de Custo
    cost_center_data = Employee.objects.filter(
        company=company,
        status='ACTIVE'
    ).values('centro_de_custo').annotate(count=Count('id')).order_by('-count')
    
    return {
        'company': company,
        'total_employees': total_employees,
        'active_forms_count': active_forms_count,
        'form_metrics': form_metrics,
        'climate_score': round(climate_score, 2) if climate_score else None,
        'wellbeing_score': round(wellbeing_score, 2) if wellbeing_score else None,
        'sector_data': list(sector_data),
        'cost_center_data': list(cost_center_data),
    }


@login_required
@require_company_admin
def report_dashboard(request):
    """Dashboard com metricas gerais da empresa."""
    company = request.user.company
    context = get_dashboard_data(company)
    return render(request, 'reports/dashboard.html', context)


@login_required
@require_admin_master
def admin_company_dashboard(request, company_pk):
    """Dashboard de uma empresa específica visto pelo ADMIN_MASTER."""
    from companies.models import Company
    company = get_object_or_404(Company, pk=company_pk)
    
    # Injeta a empresa no request para o context_processor de logo/cores
    request.current_company = company
    
    context = get_dashboard_data(company)
    context['is_admin_view'] = True
    
    return render(request, 'reports/dashboard.html', context)


@login_required
@require_company_admin
def generate_form_report(request, form_pk):
    """Gera relatorio PDF para um formulario."""
    company = request.user.company
    form_instance = get_object_or_404(FormInstance, pk=form_pk, company=company)
    
    questions = form_instance.template.questions.all().order_by('order')
    
    question_results = []
    for question in questions:
        answers = FormAnswer.objects.filter(
            assignment__form_instance=form_instance,
            question=question
        )
        
        result = {
            'question': question,
            'total_answers': answers.count(),
        }
        
        if question.question_type in ['SCALE', 'SCALE_10']:
            avg = answers.aggregate(avg=Avg('numeric_value'))['avg']
            result['average'] = round(avg, 2) if avg else None
            
            distribution = {}
            max_val = 5 if question.question_type == 'SCALE' else 10
            for i in range(1, max_val + 1):
                count = answers.filter(numeric_value=i).count()
                distribution[i] = count
            result['distribution'] = distribution
            
        elif question.question_type == 'YESNO':
            yes_count = answers.filter(boolean_value=True).count()
            no_count = answers.filter(boolean_value=False).count()
            result['yes_count'] = yes_count
            result['no_count'] = no_count
            
        elif question.question_type in ['SINGLE', 'MULTIPLE']:
            option_counts = {}
            for answer in answers:
                if answer.selected_options:
                    for opt in answer.selected_options:
                        option_counts[opt] = option_counts.get(opt, 0) + 1
            result['option_counts'] = option_counts
        
        question_results.append(result)
    
    stats = {
        'total_assigned': form_instance.assignments.count(),
        'total_completed': form_instance.assignments.filter(status='COMPLETED').count(),
        'response_rate': form_instance.get_response_rate(),
        'average_score': form_instance.get_average_score(),
    }
    
    context = {
        'company': company,
        'form_instance': form_instance,
        'question_results': question_results,
        'stats': stats,
        'generated_at': timezone.now(),
        'is_anonymous': form_instance.is_anonymous,
    }
    
    html_string = render_to_string('reports/pdf/form_report.html', context)
    
    try:
        from weasyprint import HTML
        html = HTML(string=html_string, base_url=request.build_absolute_uri('/'))
        pdf = html.write_pdf()
    except ImportError as e:
        messages.error(request, f"Erro de sistema: Biblioteca ausente ({str(e)}). O administrador já foi notificado.")
        return redirect('reports:list')
    except Exception as e:
        messages.error(request, f"Erro ao gerar PDF: {str(e)}")
        return redirect('reports:list')
    
    report = Report.objects.create(
        company=company,
        title=f"Relatorio - {form_instance.title}",
        report_type='FORM_RESULTS',
        form_instance=form_instance,
        period_start=form_instance.start_date.date(),
        period_end=form_instance.end_date.date(),
        results_data={
            'stats': stats,
            'question_count': len(question_results)
        },
        created_by=request.user
    )
    
    AuditLog.log(
        user=request.user,
        action='EXPORT',
        description=f'Relatorio PDF gerado para "{form_instance.title}"',
        obj=report,
        request=request
    )
    
    response = HttpResponse(pdf, content_type='application/pdf')
    filename = f"relatorio_{form_instance.pk}_{timezone.now().strftime('%Y%m%d')}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response


@login_required
@require_company_admin
def generate_simdcconr01_report(request, form_pk):
    """
    Gera o Laudo Pericial Integrado SIMDCCONR01 usando o Motor de Texto Determinístico.
    Substitui a análise por IA com rastreabilidade total.
    """
    company = request.user.company
    form_instance = get_object_or_404(
        FormInstance,
        pk=form_pk,
        company=company,
        template__category='SIMDCCONR01'
    )

    from .engine_text import TextEngine
    from .utils_charts import generate_radar_chart_svg, generate_heatmap_svg, generate_bar_chart_svg

    engine = TextEngine()
    laudo_data = engine.generate_organizational_laudo(form_instance)

    # Gerar Gráficos SVG
    chart_radar = generate_radar_chart_svg(laudo_data['chart_data'].get('radar', {}), size=300)
    chart_heatmap = generate_heatmap_svg(laudo_data['chart_data'].get('heatmap', {}), width=400)
    chart_bars = generate_bar_chart_svg(laudo_data['chart_data'].get('likert_distribution', {}), width=400)

    context = {
        'laudo_data': laudo_data,
        'form_instance': form_instance,
        'generated_at': timezone.now(),
        'chart_radar': chart_radar,
        'chart_heatmap': chart_heatmap,
        'chart_bars': chart_bars,
    }

    html_string = render_to_string('reports/pdf/laudo_organizacional.html', context)
    try:
        from weasyprint import HTML
        html = HTML(string=html_string, base_url=request.build_absolute_uri('/'))
        pdf = html.write_pdf()
    except ImportError as e:
        messages.error(request, f"Erro de sistema: Biblioteca ausente ({str(e)}).")
        return redirect('reports:dashboard')
    except Exception as e:
        messages.error(request, f"Erro ao gerar PDF: {str(e)}")
        return redirect('reports:dashboard')

    # Log de auditoria
    AuditLog.log(
        user=request.user,
        action='EXPORT',
        description=f'Laudo Pericial Organizacional gerado para "{form_instance.title}"',
        obj=form_instance,
        request=request
    )

    response = HttpResponse(pdf, content_type='application/pdf')
    filename = f"laudo_organizacional_{form_instance.pk}_{timezone.now().strftime('%Y%m%d')}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@login_required
@require_company_admin
def download_individual_pdf(request, form_pk, assignment_pk):
    """
    Gera PDF de devolutiva individual (Respondente) — 160 itens.
    Nível 1 da hierarquia de saída.
    """
    company = request.user.company
    form_instance = get_object_or_404(
        FormInstance,
        pk=form_pk,
        company=company,
        template__category='SIMDCCONR01'
    )
    assignment = get_object_or_404(
        FormAssignment,
        pk=assignment_pk,
        form_instance=form_instance,
        status='COMPLETED'
    )

    from .engine_text import TextEngine
    from .utils_charts import generate_radar_chart_svg

    engine = TextEngine()
    report_data = engine.generate_respondent_report(assignment)

    # Radar chart com dimensões
    radar_data = {}
    for dim in report_data.get('dimension_summary', []):
        if dim['instrumento'] == 'IMCO':
            radar_data[dim['dimensao']] = dim['media']
    chart_radar = generate_radar_chart_svg(radar_data, size=280)

    context = {
        'company': company,
        'form_instance': form_instance,
        'assignment': assignment,
        'report_data': report_data,
        'chart_radar': chart_radar,
        'generated_at': timezone.now(),
    }

    html_string = render_to_string('reports/pdf/individual_respondente.html', context)
    try:
        from weasyprint import HTML
        html = HTML(string=html_string, base_url=request.build_absolute_uri('/'))
        pdf = html.write_pdf()
    except ImportError as e:
        messages.error(request, f"Erro de sistema: Biblioteca ausente ({str(e)}).")
        return redirect('reports:dashboard')
    except Exception as e:
        messages.error(request, f"Erro ao gerar devolutiva individual: {str(e)}")
        return redirect('reports:dashboard')

    AuditLog.log(
        user=request.user,
        action='EXPORT',
        description=f'Devolutiva individual gerada para {assignment.employee.nome}',
        obj=assignment,
        request=request
    )

    response = HttpResponse(pdf, content_type='application/pdf')
    filename = f"devolutiva_{assignment.employee.pk}_{timezone.now().strftime('%Y%m%d')}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@login_required
@require_company_admin
def download_pcmso_pdf(request, form_pk, assignment_pk):
    """
    Gera PDF do Anexo Individual Obrigatório ao PCMSO.
    Nível 1.5 — deve ser anexado a ficha admissional, prontuário e PCMSO.
    """
    company = request.user.company
    form_instance = get_object_or_404(
        FormInstance,
        pk=form_pk,
        company=company,
        template__category='SIMDCCONR01'
    )
    assignment = get_object_or_404(
        FormAssignment,
        pk=assignment_pk,
        form_instance=form_instance,
        status='COMPLETED'
    )

    from .engine_text import TextEngine

    engine = TextEngine()
    pcmso_data = engine.generate_pcmso_annex(assignment)

    # Tenta associar laudo individual para assinatura
    diagnostic = None
    if hasattr(assignment, 'diagnostic'):
        diagnostic = assignment.diagnostic

    context = {
        'company': company,
        'form_instance': form_instance,
        'assignment': assignment,
        'pcmso_data': pcmso_data,
        'diagnostic': diagnostic,
        'generated_at': timezone.now(),
    }

    html_string = render_to_string('reports/pdf/anexo_pcmso.html', context)
    try:
        from weasyprint import HTML
        html = HTML(string=html_string, base_url=request.build_absolute_uri('/'))
        pdf = html.write_pdf()
    except ImportError as e:
        messages.error(request, f"Erro de sistema: Biblioteca ausente ({str(e)}).")
        return redirect('reports:dashboard')
    except Exception as e:
        messages.error(request, f"Erro ao gerar PDF: {str(e)}")
        return redirect('reports:dashboard')

    AuditLog.log(
        user=request.user,
        action='EXPORT',
        description=f'Anexo PCMSO gerado para {assignment.employee.nome}',
        obj=assignment,
        request=request
    )

    response = HttpResponse(pdf, content_type='application/pdf')
    filename = f"pcmso_{assignment.employee.pk}_{timezone.now().strftime('%Y%m%d')}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@login_required
@require_company_admin
def download_organizational_pdf(request, form_pk):
    """
    Gera PDF do Laudo Pericial Organizacional completo.
    Nível 3 — inclui SESMT, PGR/GRO, PCMSO, NR-17, NR-12.
    Alias para generate_simdcconr01_report com template atualizado.
    """
    return generate_simdcconr01_report(request, form_pk)


@login_required
def sign_report(request, validation_code):
    """Permite que o psicólogo assine o laudo."""
    diagnostic = get_object_or_404(EmployeeDiagnostic, validation_code=validation_code)
    
    if request.method == 'POST':
        method = request.POST.get('method')
        
        diagnostic.is_signed = True
        diagnostic.signed_by = request.user
        diagnostic.signature_method = method
        diagnostic.signature_timestamp = timezone.now()
        
        if method == 'GOVBR':
            diagnostic.govbr_token = "VALIDADO-VIA-GOVBR-" + str(timezone.now().timestamp())
            
        diagnostic.save()
        
        AuditLog.log(
            user=request.user,
            action='EXPORT',
            description=f'Laudo {validation_code} assinado via {method}',
            obj=diagnostic,
            request=request
        )
        
        messages.success(request, 'Documento assinado com sucesso!')
        return redirect('reports:view_diagnostic', validation_code=validation_code)
        
    return render(request, 'reports/sign_report.html', {
        'diagnostic': diagnostic
    })


@login_required
@require_company_admin
def generate_period_report(request):
    """Gera relatorio de periodo."""
    company = request.user.company
    
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    if not start_date or not end_date:
        messages.error(request, 'Selecione o periodo.')
        return redirect('reports:dashboard')
    
    forms = FormInstance.objects.filter(
        company=company,
        start_date__gte=start_date,
        end_date__lte=end_date
    )
    
    form_summaries = []
    for form in forms:
        summary = {
            'form': form,
            'category': form.template.get_category_display(),
            'response_rate': form.get_response_rate(),
            'avg_score': form.get_average_score(),
            'total_responses': form.assignments.filter(status='COMPLETED').count(),
        }
        form_summaries.append(summary)
    
    climate_avg = FormAnswer.objects.filter(
        assignment__form_instance__company=company,
        assignment__form_instance__template__category='CLIMATE',
        assignment__form_instance__start_date__gte=start_date,
        assignment__form_instance__end_date__lte=end_date,
        question__question_type__in=['SCALE', 'SCALE_10']
    ).aggregate(avg=Avg('numeric_value'))['avg']
    
    wellbeing_avg = FormAnswer.objects.filter(
        assignment__form_instance__company=company,
        assignment__form_instance__template__category='WELLBEING',
        assignment__form_instance__start_date__gte=start_date,
        assignment__form_instance__end_date__lte=end_date,
        question__question_type__in=['SCALE', 'SCALE_10']
    ).aggregate(avg=Avg('numeric_value'))['avg']
    
    context = {
        'company': company,
        'start_date': start_date,
        'end_date': end_date,
        'form_summaries': form_summaries,
        'climate_avg': round(climate_avg, 2) if climate_avg else None,
        'wellbeing_avg': round(wellbeing_avg, 2) if wellbeing_avg else None,
        'generated_at': timezone.now(),
    }
    
    html_string = render_to_string('reports/pdf/period_report.html', context)
    
    try:
        from weasyprint import HTML
        html = HTML(string=html_string, base_url=request.build_absolute_uri('/'))
        pdf = html.write_pdf()
    except ImportError as e:
        messages.error(request, f"Erro de sistema: Biblioteca ausente ({str(e)}).")
        return redirect('reports:dashboard')
    except Exception as e:
        messages.error(request, f"Erro ao gerar PDF de período: {str(e)}")
        return redirect('reports:dashboard')
    
    response = HttpResponse(pdf, content_type='application/pdf')
    filename = f"relatorio_periodo_{start_date}_{end_date}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response

def validate_diagnostic(request, validation_code=None):
    """View publica para validacao de Laudos via Codigo."""
    from .models import EmployeeDiagnostic
    import uuid
    
    diagnostic = None
    error = None
    
    # Se recebeu via GET form (input name='code')
    code = request.GET.get('code', validation_code)
    
    if code:
        try:
            val_uuid = uuid.UUID(code)
            diagnostic = EmployeeDiagnostic.objects.get(validation_code=val_uuid)
        except (ValueError, EmployeeDiagnostic.DoesNotExist):
            error = "Codigo invalido ou laudo nao encontrado."
            
    return render(request, 'reports/validate.html', {
        'diagnostic': diagnostic,
        'error': error,
        'searched_code': code,
    })


@login_required
def view_diagnostic(request, validation_code):
    """View restrita para leitura do Laudo."""
    if request.user.role != 'ADMIN_MASTER':
        messages.error(request, 'Acesso restrito a administradores SaaS.')
        return redirect('accounts:dashboard')
        
    from .models import EmployeeDiagnostic
    from .engine_text import TextEngine
    import uuid
    
    try:
        val_uuid = uuid.UUID(validation_code)
        diagnostic = get_object_or_404(EmployeeDiagnostic, validation_code=val_uuid)
    except ValueError:
        messages.error(request, 'Codigo invalido.')
        return redirect('accounts:admin_laudos')
        
    # Gerar dados reais do motor determinístico para o gráfico e referências
    engine = TextEngine()
    report_data = engine.generate_respondent_report(diagnostic.assignment)
    
    return render(request, 'reports/diagnostic_view.html', {
        'diagnostic': diagnostic,
        'report_data': report_data
    })

