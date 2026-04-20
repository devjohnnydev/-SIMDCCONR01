"""
Views para gestao de formularios e respostas.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Avg, Count

from .models import FormTemplate, FormQuestion, FormInstance, FormAssignment, FormAnswer
from .forms import FormInstanceForm, FormQuestionFormSet
from companies.views import require_company_admin
from employees.models import Employee
from audit.models import AuditLog


@login_required
@require_company_admin
def template_list(request):
    """Lista templates de formularios disponiveis."""
    company = request.user.company
    
    global_templates = FormTemplate.objects.filter(is_global=True, is_active=True)
    company_templates = FormTemplate.objects.filter(company=company, is_active=True)
    
    context = {
        'global_templates': global_templates,
        'company_templates': company_templates,
    }
    return render(request, 'forms_builder/template_list.html', context)


@login_required
@require_company_admin
def template_detail(request, pk):
    """Detalhes de um template."""
    template = get_object_or_404(FormTemplate, pk=pk)
    
    if not template.is_global and template.company != request.user.company:
        messages.error(request, 'Acesso nao autorizado.')
        return redirect('forms:templates')
    
    questions = template.questions.all().order_by('order')
    
    return render(request, 'forms_builder/template_detail.html', {
        'template': template,
        'questions': questions
    })


@login_required
@require_company_admin
def form_instance_list(request):
    """Lista formularios aplicados da empresa."""
    company = request.user.company
    
    instances = FormInstance.objects.filter(company=company).select_related('template')
    
    status_filter = request.GET.get('status', '')
    if status_filter:
        instances = instances.filter(status=status_filter)
    
    context = {
        'instances': instances,
        'status_filter': status_filter,
    }
    return render(request, 'forms_builder/instance_list.html', context)


@login_required
@require_company_admin
def form_instance_create(request, template_pk):
    """Cria nova instancia de formulario a partir de um template."""
    company = request.user.company
    
    if not company.can_add_form():
        messages.error(request, 'Limite de formularios ativos do plano atingido.')
        return redirect('forms:instances')
    
    template = get_object_or_404(FormTemplate, pk=template_pk)
    
    if not template.is_global and template.company != company:
        messages.error(request, 'Acesso nao autorizado.')
        return redirect('forms:templates')
    
    if request.method == 'POST':
        form = FormInstanceForm(request.POST, company=company)
        if form.is_valid():
            instance = form.save(commit=False)
            instance.template = template
            instance.company = company
            instance.created_by = request.user
            instance.save()
            
            AuditLog.log(
                user=request.user,
                action='CREATE',
                description=f'Formulario "{instance.title}" criado',
                obj=instance,
                request=request
            )
            
            messages.success(request, 'Formulario criado com sucesso!')
            return redirect('forms:instance_detail', pk=instance.pk)
    else:
        form = FormInstanceForm(company=company, initial={
            'title': f"{template.name} - {timezone.now().strftime('%d/%m/%Y')}"
        })
    
    return render(request, 'forms_builder/instance_form.html', {
        'form': form,
        'template': template,
        'action': 'Criar'
    })


@login_required
@require_company_admin
def form_instance_detail(request, pk):
    """Detalhes de um formulario aplicado."""
    company = request.user.company
    instance = get_object_or_404(FormInstance, pk=pk, company=company)
    
    assignments = instance.assignments.select_related('employee').order_by('-completed_at', 'employee__nome')
    
    stats = {
        'total': assignments.count(),
        'completed': assignments.filter(status='COMPLETED').count(),
        'pending': assignments.filter(status='PENDING').count(),
        'in_progress': assignments.filter(status='IN_PROGRESS').count(),
        'response_rate': instance.get_response_rate(),
    }
    
    question_stats = []
    for question in instance.template.questions.all():
        if question.question_type in ['SCALE', 'SCALE_10']:
            avg = FormAnswer.objects.filter(
                assignment__form_instance=instance,
                question=question
            ).aggregate(avg=Avg('numeric_value'))['avg']
            question_stats.append({
                'question': question,
                'avg': round(avg, 2) if avg else None
            })
    
    context = {
        'instance': instance,
        'assignments': assignments,
        'stats': stats,
        'question_stats': question_stats,
    }
    return render(request, 'forms_builder/instance_detail.html', context)


@login_required
@require_company_admin
def form_instance_publish(request, pk):
    """Publica um formulario e cria atribuicoes."""
    company = request.user.company
    instance = get_object_or_404(FormInstance, pk=pk, company=company)
    
    if instance.status != 'DRAFT':
        messages.warning(request, 'Este formulario ja foi publicado.')
        return redirect('forms:instance_detail', pk=pk)
    
    instance.publish()
    
    AuditLog.log(
        user=request.user,
        action='PUBLISH',
        description=f'Formulario "{instance.title}" publicado',
        obj=instance,
        request=request
    )
    
    messages.success(
        request,
        f'Formulario publicado! {instance.assignments.count()} funcionarios foram notificados.'
    )
    return redirect('forms:instance_detail', pk=pk)
    

@login_required
@require_company_admin
def form_instance_resync(request, pk):
    """Sincroniza e garante que todos os funcionarios ativos tenham o formulario."""
    company = request.user.company
    instance = get_object_or_404(FormInstance, pk=pk, company=company)
    
    if instance.status != 'ACTIVE':
        messages.warning(request, 'O formulário precisa estar Ativo para sincronizar participantes.')
        return redirect('forms:instance_detail', pk=pk)
    
    from employees.models import Employee
    employees = Employee.objects.filter(company=company, status='ACTIVE')
    count = 0
    for employee in employees:
        _, created = FormAssignment.objects.get_or_create(
            employee=employee,
            form_instance=instance,
            defaults={'status': 'PENDING'}
        )
        if created:
            count += 1
            
    messages.success(request, f'Sincronização concluída! {count} novos funcionários vinculados.')
    return redirect('forms:instance_detail', pk=pk)


@login_required
@require_company_admin
def form_instance_close(request, pk):
    """Encerra um formulario."""
    company = request.user.company
    instance = get_object_or_404(FormInstance, pk=pk, company=company)
    
    instance.status = 'CLOSED'
    instance.save()
    
    AuditLog.log(
        user=request.user,
        action='UPDATE',
        description=f'Formulario "{instance.title}" encerrado',
        obj=instance,
        request=request
    )
    
    messages.success(request, 'Formulario encerrado.')
    return redirect('forms:instance_detail', pk=pk)


@login_required
def form_respond(request, assignment_pk):
    """Pagina para funcionario responder formulario."""
    assignment = get_object_or_404(
        FormAssignment,
        pk=assignment_pk
    )
    
    if hasattr(request.user, 'employee_profile'):
        employee = request.user.employee_profile
    else:
        employee = Employee.objects.filter(
            email=request.user.email,
            company=request.user.company
        ).first()
    
    if not employee or assignment.employee != employee:
        messages.error(request, 'Voce nao tem permissao para responder este formulario.')
        return redirect('accounts:dashboard')
    
    if assignment.status == 'COMPLETED':
        messages.info(request, 'Voce ja respondeu este formulario.')
        return redirect('accounts:employee_dashboard')
    
    instance = assignment.form_instance
    
    if not instance.is_active:
        messages.warning(request, 'Este formulario nao esta mais disponivel.')
        return redirect('accounts:employee_dashboard')
    
    questions = instance.template.questions.all().order_by('analysis_category', 'order')

    # Agrupar perguntas por categoria de análise
    from collections import OrderedDict
    CATEGORY_ORDER = ['DIAGNOSTICO', 'DISSONANCIA', 'RISCOS', 'RECOMENDACOES']
    CATEGORY_META = {
        'DIAGNOSTICO': {'label': 'Diagnóstico Psicossocial', 'icon': 'bi-activity', 'color': '#3b82f6', 'number': 1},
        'DISSONANCIA': {'label': 'Dissonância de Clima e Cultura', 'icon': 'bi-people', 'color': '#64748b', 'number': 2},
        'RISCOS': {'label': 'Riscos Identificados (PGR/GRO)', 'icon': 'bi-exclamation-triangle', 'color': '#f59e0b', 'number': 3},
        'RECOMENDACOES': {'label': 'Recomendações de Ação', 'icon': 'bi-list-check', 'color': '#10b981', 'number': 4},
    }
    grouped_questions = OrderedDict()
    for cat in CATEGORY_ORDER:
        cat_questions = [q for q in questions if q.analysis_category == cat]
        if cat_questions:
            grouped_questions[cat] = {
                'meta': CATEGORY_META[cat],
                'questions': cat_questions,
            }
    
    # Notificar início do preenchimento (primeiro acesso)
    assignment.start()
    
    if request.method == 'POST':
        
        all_valid = True
        for question in questions:
            answer_key = f'question_{question.pk}'
            value = request.POST.get(answer_key, '')
            
            if question.is_required and not value:
                all_valid = False
                messages.error(request, f'A pergunta "{question.text[:50]}..." e obrigatoria.')
                break
            
            answer, created = FormAnswer.objects.get_or_create(
                assignment=assignment,
                question=question
            )
            
            if question.question_type in ['SCALE', 'SCALE_10', 'NUMBER']:
                answer.numeric_value = float(value) if value else None
            elif question.question_type == 'YESNO':
                answer.boolean_value = value.lower() == 'sim' if value else None
            elif question.question_type == 'DATE':
                answer.date_value = value if value else None
            elif question.question_type in ['MULTIPLE']:
                answer.selected_options = request.POST.getlist(answer_key)
            elif question.question_type == 'SINGLE':
                answer.selected_options = [value] if value else []
            else:
                answer.text_value = value
            
            if instance.is_anonymous:
                answer.anonymous_employee = employee
            
            answer.save()
        
        if all_valid:
            assignment.complete()
            
            AuditLog.log(
                user=request.user,
                action='SUBMIT',
                description=f'Formulario "{instance.title}" respondido',
                obj=assignment,
                request=request,
                company=instance.company
            )
            
            messages.success(request, 'Formulario enviado com sucesso! Obrigado pela sua participacao.')
            return redirect('accounts:employee_dashboard')
    
    context = {
        'assignment': assignment,
        'instance': instance,
        'questions': questions,
        'grouped_questions': grouped_questions,
    }
    return render(request, 'forms_builder/form_respond.html', context)


@login_required
def form_view_responses(request, assignment_pk):
    """Visualiza respostas de um formulario."""
    assignment = get_object_or_404(FormAssignment, pk=assignment_pk)
    
    if request.user.is_company_admin and assignment.form_instance.company == request.user.company:
        if assignment.form_instance.is_anonymous:
            messages.error(request, 'Este formulário é anônimo. Você pode ver apenas quem participou, mas não as respostas individuais.')
            return redirect('forms:instance_detail', pk=assignment.form_instance.pk)
        pass
    elif hasattr(request.user, 'employee_profile') and assignment.employee == request.user.employee_profile:
        pass
    else:
        messages.error(request, 'Acesso nao autorizado.')
        return redirect('accounts:dashboard')
    
    answers = assignment.answers.select_related('question').order_by('question__order')
    
    return render(request, 'forms_builder/view_responses.html', {
        'assignment': assignment,
        'answers': answers
    })


@login_required
@require_company_admin
def resend_form_notification(request, assignment_pk=None, employee_id=None):
    """Reenvia o e-mail de notificação de um formulário para o funcionário."""
    from .utils_emails import send_form_publication_notification
    
    if assignment_pk:
        assignment = get_object_or_404(FormAssignment, pk=assignment_pk, form_instance__company=request.user.company)
    elif employee_id:
        from employees.models import Employee
        employee = get_object_or_404(Employee, pk=employee_id, company=request.user.company)
        assignment = employee.get_pending_assignment()
        if not assignment:
            messages.warning(request, f'O funcionário {employee.nome} não possui pesquisas pendentes no momento.')
            return redirect(request.META.get('HTTP_REFERER', 'employees:list'))
    else:
        return redirect('forms:instances')
    
    if assignment.status == 'COMPLETED':
        messages.warning(request, 'Este funcionário já concluiu a pesquisa.')
    else:
        success = send_form_publication_notification(assignment)
        if success:
            messages.success(request, f'Convite reenviado com sucesso para {assignment.employee.nome}!')
        else:
            messages.error(request, 'Erro ao enviar o e-mail. Verifique o cadastro do funcionário.')
            
    return redirect(request.META.get('HTTP_REFERER', 'forms:instances'))


@login_required
@require_company_admin
def template_create(request):
    """Cria um novo template de formulário do zero."""
    company = request.user.company

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        category = request.POST.get('category', 'CUSTOM')

        if not name:
            messages.error(request, 'O nome do template é obrigatório.')
            return redirect('forms:template_create')

        template = FormTemplate.objects.create(
            name=name,
            description=description,
            category=category,
            company=company,
            is_global=request.user.role == 'ADMIN_MASTER',
            is_active=True
        )

        AuditLog.log(
            user=request.user,
            action='CREATE',
            description=f'Template "{name}" criado',
            obj=template,
            request=request
        )

        messages.success(request, f'Template "{name}" criado com sucesso! Adicione suas perguntas.')
        return redirect('forms:template_detail', pk=template.pk)

    return render(request, 'forms_builder/template_create.html', {
        'category_choices': FormTemplate.CATEGORY_CHOICES,
        'analysis_categories': FormQuestion.ANALYSIS_CATEGORY_CHOICES,
    })


@login_required
@require_company_admin
def question_add(request, template_pk):
    """Adiciona uma nova pergunta a um template."""
    template = get_object_or_404(FormTemplate, pk=template_pk)

    if not template.is_global and template.company != request.user.company:
        messages.error(request, 'Acesso não autorizado.')
        return redirect('forms:templates')

    if request.method == 'POST':
        text = request.POST.get('text', '').strip()
        question_type = request.POST.get('question_type', 'SCALE')
        analysis_category = request.POST.get('analysis_category', 'DIAGNOSTICO')
        is_required = request.POST.get('is_required') == 'on'
        help_text = request.POST.get('help_text', '').strip()
        options_raw = request.POST.get('options', '').strip()

        if not text:
            messages.error(request, 'O texto da pergunta é obrigatório.')
            return redirect('forms:template_detail', pk=template_pk)

        # Calcular próxima ordem
        last_order = template.questions.order_by('-order').values_list('order', flat=True).first() or 0

        options = []
        if options_raw and question_type in ('MULTIPLE', 'SINGLE'):
            options = [o.strip() for o in options_raw.split('\n') if o.strip()]

        FormQuestion.objects.create(
            template=template,
            text=text,
            question_type=question_type,
            analysis_category=analysis_category,
            options=options,
            order=last_order + 1,
            is_required=is_required,
            help_text=help_text
        )

        messages.success(request, 'Pergunta adicionada com sucesso!')
        return redirect('forms:template_detail', pk=template_pk)

    return redirect('forms:template_detail', pk=template_pk)


@login_required
@require_company_admin
def question_edit(request, question_pk):
    """Edita uma pergunta existente."""
    question = get_object_or_404(FormQuestion, pk=question_pk)
    template = question.template

    if not template.is_global and template.company != request.user.company:
        messages.error(request, 'Acesso não autorizado.')
        return redirect('forms:templates')

    if request.method == 'POST':
        question.text = request.POST.get('text', question.text).strip()
        question.question_type = request.POST.get('question_type', question.question_type)
        question.analysis_category = request.POST.get('analysis_category', question.analysis_category)
        question.is_required = request.POST.get('is_required') == 'on'
        question.help_text = request.POST.get('help_text', '').strip()
        question.order = int(request.POST.get('order', question.order))

        options_raw = request.POST.get('options', '').strip()
        if options_raw and question.question_type in ('MULTIPLE', 'SINGLE'):
            question.options = [o.strip() for o in options_raw.split('\n') if o.strip()]

        question.save()
        messages.success(request, 'Pergunta atualizada com sucesso!')

    return redirect('forms:template_detail', pk=template.pk)


@login_required
@require_company_admin
def question_delete(request, question_pk):
    """Exclui uma pergunta do template."""
    question = get_object_or_404(FormQuestion, pk=question_pk)
    template = question.template

    if not template.is_global and template.company != request.user.company:
        messages.error(request, 'Acesso não autorizado.')
        return redirect('forms:templates')

    if request.method == 'POST':
        question.delete()
        messages.success(request, 'Pergunta removida com sucesso!')

    return redirect('forms:template_detail', pk=template.pk)
