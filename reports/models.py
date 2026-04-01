import uuid
from django.db import models


class Report(models.Model):
    """
    Registro de relatorios gerados.
    Armazena metadados e referencia ao arquivo PDF.
    """
    
    TYPE_CHOICES = [
        ('FORM_RESULTS', 'Resultados de Formulario'),
        ('PERIOD_SUMMARY', 'Resumo do Periodo'),
        ('CLIMATE_INDEX', 'Indice de Clima'),
        ('WELLBEING_INDEX', 'Indice de Bem-estar'),
        ('NR01_COMPLIANCE', 'Compliance NR-01'),
        ('SIMDCCONR01', 'Laudo Integrado SIMDCCONR01'),
        ('LAUDO_PERICIAL', 'Laudo Pericial Assinado'),
        ('CUSTOM', 'Personalizado'),
    ]
    
    is_signed = models.BooleanField('Assinado Digitalmente', default=False)
    signature_data = models.JSONField('Dados da Assinatura', default=dict, blank=True)
    signature_date = models.DateTimeField('Data da Assinatura', null=True, blank=True)
    
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='reports',
        verbose_name='Empresa'
    )
    
    title = models.CharField('Titulo', max_length=200)
    report_type = models.CharField('Tipo', max_length=20, choices=TYPE_CHOICES)
    description = models.TextField('Descricao', blank=True)
    
    form_instance = models.ForeignKey(
        'forms_builder.FormInstance',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reports',
        verbose_name='Formulario'
    )
    
    period_start = models.DateField('Periodo Inicio', null=True, blank=True)
    period_end = models.DateField('Periodo Fim', null=True, blank=True)
    
    file = models.FileField('Arquivo PDF', upload_to='reports/', null=True, blank=True)
    
    parameters = models.JSONField('Parametros', default=dict, blank=True)
    results_data = models.JSONField('Dados do Resultado', default=dict, blank=True)
    
    created_at = models.DateTimeField('Gerado em', auto_now_add=True)
    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='reports',
        verbose_name='Gerado por'
    )
    
    class Meta:
        verbose_name = 'Relatorio'
        verbose_name_plural = 'Relatorios'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.company.nome_fantasia}"


class EmployeeDiagnostic(models.Model):
    """
    Laudo individual de um funcionario gerado pela inteligencia artificial (Groq).
    Mantem idempotencia e permite validacao publica por um hash unico.
    """
    
    assignment = models.OneToOneField(
        'forms_builder.FormAssignment',
        on_delete=models.CASCADE,
        related_name='diagnostic',
        verbose_name='Formulario Respondido'
    )
    
    validation_code = models.UUIDField(
        'Codigo de Validacao', 
        default=uuid.uuid4, 
        editable=False, 
        unique=True
    )
    
    diagnostic_data = models.JSONField('Dados do Laudo (Groq)', default=dict)
    
    generated_at = models.DateTimeField('Gerado em', auto_now_add=True)
    
    # Electronic Signature and Assignment
    assigned_professional = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_diagnostics',
        verbose_name='Signatario Atribuido'
    )
    is_signed = models.BooleanField('Assinado', default=False)
    signed_by = models.ForeignKey(
        'accounts.User', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='signed_diagnostics_final'
    )
    signature_method = models.CharField(
        'Metodo de Assinatura', 
        max_length=20, 
        choices=[('INTERNAL', 'Interna'), ('GOVBR', 'Gov.br'), ('MANUAL', 'Manual')],
        blank=True
    )
    signature_timestamp = models.DateTimeField('Data da Assinatura', null=True, blank=True)
    govbr_token = models.CharField('Token Gov.br', max_length=255, blank=True)
    
    class Meta:
        verbose_name = 'Laudo Individual'
        verbose_name_plural = 'Laudos Individuais'
        ordering = ['-generated_at']
        
    def __str__(self):
        return f"Laudo {self.validation_code} - {self.assignment.employee.nome}"
