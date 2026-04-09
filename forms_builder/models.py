"""
Sistema flexivel de formularios para NR-01, Clima e Bem-estar.
Suporta templates, perguntas de varios tipos e respostas anonimas.
"""
from django.db import models
from django.utils import timezone


class FormTemplate(models.Model):
    """
    Template de formulario que pode ser global ou especifico de uma empresa.
    Serve como base para criar instancias de formularios.
    """
    
    CATEGORY_CHOICES = [
        ('NR01', 'NR-01 - Riscos Ocupacionais'),
        ('CLIMATE', 'Clima Organizacional'),
        ('WELLBEING', 'Bem-estar no Trabalho'),
        ('SIMDCCONR01', 'Sistema Integrado SIMDCCONR01'),
        ('CUSTOM', 'Personalizado'),
    ]
    
    name = models.CharField('Nome do Template', max_length=200)
    description = models.TextField('Descricao', blank=True)
    category = models.CharField('Categoria', max_length=20, choices=CATEGORY_CHOICES)
    
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='form_templates',
        verbose_name='Empresa',
        help_text='Deixe vazio para templates globais'
    )
    
    is_global = models.BooleanField('Template Global', default=False)
    is_active = models.BooleanField('Ativo', default=True)
    
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)
    
    class Meta:
        verbose_name = 'Template de Formulario'
        verbose_name_plural = 'Templates de Formularios'
        ordering = ['category', 'name']
    
    def __str__(self):
        scope = "Global" if self.is_global else (self.company.nome_fantasia if self.company else "Sem empresa")
        return f"{self.name} ({self.get_category_display()}) - {scope}"
    
    def clone_for_company(self, company):
        """Clona o template para uma empresa especifica."""
        new_template = FormTemplate.objects.create(
            name=self.name,
            description=self.description,
            category=self.category,
            company=company,
            is_global=False,
            is_active=True
        )
        
        for question in self.questions.all():
            FormQuestion.objects.create(
                template=new_template,
                text=question.text,
                question_type=question.question_type,
                options=question.options,
                order=question.order,
                is_required=question.is_required,
                help_text=question.help_text
            )
        
        return new_template


class FormQuestion(models.Model):
    """Pergunta de um template de formulario."""
    
    TYPE_CHOICES = [
        ('SCALE', 'Escala (1-5)'),
        ('SCALE_10', 'Escala (1-10)'),
        ('MULTIPLE', 'Multipla Escolha'),
        ('SINGLE', 'Escolha Unica'),
        ('TEXT', 'Texto Aberto'),
        ('YESNO', 'Sim/Nao'),
        ('DATE', 'Data'),
        ('NUMBER', 'Numero'),
    ]
    
    template = models.ForeignKey(
        FormTemplate,
        on_delete=models.CASCADE,
        related_name='questions',
        verbose_name='Template'
    )
    
    text = models.TextField('Texto da Pergunta')
    question_type = models.CharField('Tipo de Resposta', max_length=20, choices=TYPE_CHOICES)
    options = models.JSONField(
        'Opcoes',
        default=list,
        blank=True,
        help_text='Lista de opcoes para multipla escolha'
    )
    
    order = models.PositiveIntegerField('Ordem', default=0)
    is_required = models.BooleanField('Obrigatoria', default=True)
    help_text = models.CharField('Texto de Ajuda', max_length=500, blank=True)
    
    class Meta:
        verbose_name = 'Pergunta'
        verbose_name_plural = 'Perguntas'
        ordering = ['template', 'order']
    
    def __str__(self):
        return f"{self.order}. {self.text[:50]}..."


class FormInstance(models.Model):
    """
    Instancia de um formulario aplicado a uma empresa.
    Define periodo de coleta e configuracoes especificas.
    """
    
    STATUS_CHOICES = [
        ('DRAFT', 'Rascunho'),
        ('ACTIVE', 'Ativo'),
        ('CLOSED', 'Encerrado'),
        ('CANCELLED', 'Cancelado'),
    ]
    
    template = models.ForeignKey(
        FormTemplate,
        on_delete=models.PROTECT,
        related_name='instances',
        verbose_name='Template'
    )
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='form_instances',
        verbose_name='Empresa'
    )
    
    title = models.CharField('Titulo', max_length=200)
    description = models.TextField('Descricao', blank=True)
    
    is_anonymous = models.BooleanField(
        'Anonimo',
        default=False,
        help_text='Se ativado, respostas nao serao vinculadas aos funcionarios'
    )
    
    start_date = models.DateTimeField('Data de Inicio')
    end_date = models.DateTimeField('Data de Termino')
    
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    
    target_sectors = models.JSONField(
        'Setores Alvo',
        default=list,
        blank=True,
        help_text='Lista de setores. Vazio = todos'
    )
    target_positions = models.JSONField(
        'Cargos Alvo',
        default=list,
        blank=True,
        help_text='Lista de cargos. Vazio = todos'
    )
    
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_forms',
        verbose_name='Criado por'
    )
    
    class Meta:
        verbose_name = 'Formulario Aplicado'
        verbose_name_plural = 'Formularios Aplicados'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.company.nome_fantasia}"
    
    @property
    def is_active(self):
        """Verifica se o formulario esta ativo e dentro do periodo."""
        now = timezone.now()
        return self.status == 'ACTIVE' and self.start_date <= now <= self.end_date
    
    def get_response_rate(self):
        """Calcula a taxa de resposta."""
        total = self.assignments.count()
        if total == 0:
            return 0
        completed = self.assignments.filter(status='COMPLETED').count()
        return round((completed / total) * 100, 1)
    
    def get_average_score(self):
        """Calcula a media de respostas em escala."""
        from django.db.models import Avg
        return FormAnswer.objects.filter(
            assignment__form_instance=self,
            question__question_type__in=['SCALE', 'SCALE_10']
        ).aggregate(avg=Avg('numeric_value'))['avg']
    
    def publish(self):
        """Publica o formulario e cria atribuicoes para funcionarios."""
        from employees.models import Employee
        
        employees = Employee.objects.filter(
            company=self.company,
            status='ACTIVE'
        )
        
        if self.target_sectors:
            employees = employees.filter(setor__in=self.target_sectors)
        if self.target_positions:
            employees = employees.filter(cargo__in=self.target_positions)
        
        for employee in employees:
            FormAssignment.objects.get_or_create(
                form_instance=self,
                employee=employee,
                defaults={'status': 'PENDING'}
            )
        
        self.status = 'ACTIVE'
        self.save(update_fields=['status'])
        
        # Disparar emails para funcionários
        from .utils_emails import send_form_publication_notification
        for assignment in self.assignments.all():
            send_form_publication_notification(assignment)


class FormAssignment(models.Model):
    """Atribuicao de formulario a um funcionario."""
    
    STATUS_CHOICES = [
        ('PENDING', 'Pendente'),
        ('IN_PROGRESS', 'Em Andamento'),
        ('COMPLETED', 'Concluido'),
        ('EXPIRED', 'Expirado'),
    ]
    
    form_instance = models.ForeignKey(
        FormInstance,
        on_delete=models.CASCADE,
        related_name='assignments',
        verbose_name='Formulario'
    )
    employee = models.ForeignKey(
        'employees.Employee',
        on_delete=models.CASCADE,
        related_name='form_assignments',
        verbose_name='Funcionario'
    )
    
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default='PENDING')
    started_at = models.DateTimeField('Iniciado em', null=True, blank=True)
    completed_at = models.DateTimeField('Concluido em', null=True, blank=True)
    
    class Meta:
        verbose_name = 'Atribuicao de Formulario'
        verbose_name_plural = 'Atribuicoes de Formularios'
        unique_together = [['form_instance', 'employee']]
        ordering = ['-form_instance__created_at']
    
    def __str__(self):
        return f"{self.form_instance.title} - {self.employee.nome}"
    
    def start(self):
        """Marca o inicio do preenchimento."""
        if self.status == 'PENDING':
            self.status = 'IN_PROGRESS'
            self.started_at = timezone.now()
            self.save(update_fields=['status', 'started_at'])
            
            # Notificar empresa
            from .utils_emails import send_form_activity_notification
            send_form_activity_notification(self, activity_type='ENTRY')
    
    def complete(self):
        """Marca como concluido."""
        self.status = 'COMPLETED'
        self.completed_at = timezone.now()
        self.save(update_fields=['status', 'completed_at'])
        
        # Notificar empresa
        from .utils_emails import send_form_activity_notification
        send_form_activity_notification(self, activity_type='SUBMISSION')


class FormAnswer(models.Model):
    """Resposta individual a uma pergunta de formulario."""
    
    assignment = models.ForeignKey(
        FormAssignment,
        on_delete=models.CASCADE,
        related_name='answers',
        verbose_name='Atribuicao'
    )
    question = models.ForeignKey(
        FormQuestion,
        on_delete=models.CASCADE,
        related_name='answers',
        verbose_name='Pergunta'
    )
    
    text_value = models.TextField('Resposta Texto', blank=True)
    numeric_value = models.DecimalField(
        'Valor Numerico',
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    selected_options = models.JSONField('Opcoes Selecionadas', default=list, blank=True)
    boolean_value = models.BooleanField('Valor Booleano', null=True, blank=True)
    date_value = models.DateField('Valor Data', null=True, blank=True)
    
    anonymous_employee = models.ForeignKey(
        'employees.Employee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='anonymous_answers',
        verbose_name='Funcionario (Anonimo)',
        help_text='Usado apenas para registro de participacao em formularios anonimos'
    )
    
    created_at = models.DateTimeField('Respondido em', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Resposta'
        verbose_name_plural = 'Respostas'
        unique_together = [['assignment', 'question']]
    
    def __str__(self):
        return f"Resposta para: {self.question.text[:30]}..."
    
    def get_display_value(self):
        """Retorna o valor da resposta formatado para exibicao."""
        if self.question.question_type in ['SCALE', 'SCALE_10', 'NUMBER']:
            return str(self.numeric_value) if self.numeric_value else '-'
        elif self.question.question_type in ['MULTIPLE', 'SINGLE']:
            return ', '.join(self.selected_options) if self.selected_options else '-'
        elif self.question.question_type == 'YESNO':
            if self.boolean_value is None:
                return '-'
            return 'Sim' if self.boolean_value else 'Nao'
        elif self.question.question_type == 'DATE':
            return self.date_value.strftime('%d/%m/%Y') if self.date_value else '-'
        else:
            return self.text_value or '-'
