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

from .models import Report
from forms_builder.models import FormInstance, FormAnswer, FormQuestion
from companies.views import require_company_admin
from audit.models import AuditLog


@login_required
@require_company_admin
def report_list(request):
    """Lista relatorios gerados."""
    company = request.user.company
    reports = Report.objects.filter(company=company)
    
    return render(request, 'reports/report_list.html', {'reports': reports})


@login_required
@require_company_admin
def report_dashboard(request):
    """Dashboard com metricas gerais da empresa."""
    company = request.user.company
    
    active_forms = FormInstance.objects.filter(company=company, status='ACTIVE')
    
    total_employees = company.get_employee_count()
    active_forms_count = active_forms.count()
    
    form_metrics = []
    for form in active_forms:
        total = form.assignments.count()
        completed = form.assignments.filter(status='COMPLETED').count()
        rate = round((completed / total * 100), 1) if total > 0 else 0
        
        avg_score = FormAnswer.objects.filter(
            assignment__form_instance=form,
            question__question_type__in=['SCALE', 'SCALE_10']
        ).aggregate(avg=Avg('numeric_value'))['avg']
        
        form_metrics.append({
            'form': form,
            'total': total,
            'completed': completed,
            'response_rate': rate,
            'avg_score': round(avg_score, 2) if avg_score else None
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
    sector_data = Employee.objects.filter(
        company=company,
        status='ACTIVE'
    ).values('setor').annotate(count=Count('id')).order_by('-count')
    
    context = {
        'company': company,
        'total_employees': total_employees,
        'active_forms_count': active_forms_count,
        'form_metrics': form_metrics,
        'climate_score': round(climate_score, 2) if climate_score else None,
        'wellbeing_score': round(wellbeing_score, 2) if wellbeing_score else None,
        'sector_data': list(sector_data),
    }
    
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
    
    from weasyprint import HTML
    html = HTML(string=html_string, base_url=request.build_absolute_uri('/'))
    pdf = html.write_pdf()
    
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
    Gera o Laudo Pericial Integrado SIMDCCONR01.
    Inclui analise de IA para diagnosticos psicossociais e PGR/GRO.
    """
    company = request.user.company
    form_instance = get_object_or_404(
        FormInstance, 
        pk=form_pk, 
        company=company, 
        template__category='SIMDCCONR01'
    )
    
    # Busca a primeira atribuicao concluida para analise de IA (no prototipo)
    # Em producao, isso seria expandido para analise agregada.
    first_assignment = form_instance.assignments.filter(status='COMPLETED').first()
    
    from ai_analysis.engine import analyze_survey_results
    import json
    
    ai_results_raw = "{}"
    if first_assignment:
        ai_results_raw = analyze_survey_results(first_assignment)
    
    try:
        ai_results = json.loads(ai_results_raw)
    except:
        ai_results = {
            "diagnostico_psicossocial": "Erro no processamento de IA.",
            "dissonancia_clima_cultura": "Analise indisponivel.",
            "riscos_pgr_gro": "Consulte o SESMT.",
            "recomendacoes_acao": "Verifique os dados brutos."
        }

    # Calculos estatisticos simplificados para o laudo
    stats = {
        'total_completed': form_instance.assignments.filter(status='COMPLETED').count(),
    }
    
    imco_stats = {
        'motivacao_avg': 4.2, # Mocked for prototype demo
        'lideranca_avg': 3.8,
        'filosofia_avg': 3.5
    }
    
    context = {
        'company': company,
        'form_instance': form_instance,
        'ai_results': ai_results,
        'stats': stats,
        'imco_stats': imco_stats,
        'fdac_score': 78, # Mocked
        'nr01_risk_score': 2.4, # Mocked
        'signature_token': "SHA256-SIMDCCONR01-" + timezone.now().strftime('%Y%m%d%H%M%S'),
        'generated_at': timezone.now(),
    }
    
    html_string = render_to_string('reports/pdf/simdcconr01_report.html', context)
    from weasyprint import HTML
    html = HTML(string=html_string, base_url=request.build_absolute_uri('/'))
    pdf = html.write_pdf()
    
    return HttpResponse(pdf, content_type='application/pdf')


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
    
    from weasyprint import HTML
    html = HTML(string=html_string, base_url=request.build_absolute_uri('/'))
    pdf = html.write_pdf()
    
    response = HttpResponse(pdf, content_type='application/pdf')
    filename = f"relatorio_periodo_{start_date}_{end_date}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response
