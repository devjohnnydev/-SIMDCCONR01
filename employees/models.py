"""
Modelo de Funcionario (Employee) vinculado a uma empresa.
Suporta gestao completa de funcionarios com dados de SST.
"""
from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone


class Employee(models.Model):
    """
    Modelo de Funcionario vinculado a uma empresa.
    Pode estar vinculado a um User para acesso ao sistema.
    """
    
    STATUS_CHOICES = [
        ('ACTIVE', 'Ativo'),
        ('INACTIVE', 'Inativo'),
        ('ON_LEAVE', 'Afastado'),
        ('TERMINATED', 'Desligado'),
    ]
    
    SHIFT_CHOICES = [
        ('MORNING', 'Manha'),
        ('AFTERNOON', 'Tarde'),
        ('NIGHT', 'Noite'),
        ('FULL', 'Integral'),
        ('ROTATING', 'Revezamento'),
    ]
    
    cpf_validator = RegexValidator(
        regex=r'^\d{11}$',
        message='CPF deve conter 11 digitos numericos'
    )
    
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='employees',
        verbose_name='Empresa'
    )
    user = models.OneToOneField(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='employee_profile',
        verbose_name='Usuario'
    )
    
    nome = models.CharField('Nome Completo', max_length=200)
    email = models.EmailField('Email Corporativo')
    cpf = models.CharField('CPF', max_length=11, blank=True, validators=[cpf_validator])
    
    setor = models.CharField('Setor/Departamento', max_length=100)
    cargo = models.CharField('Cargo', max_length=100)
    turno = models.CharField('Turno', max_length=20, choices=SHIFT_CHOICES, default='FULL')
    
    data_admissao = models.DateField('Data de Admissao')
    data_nascimento = models.DateField('Data de Nascimento', null=True, blank=True)
    
    matricula = models.CharField('Matricula', max_length=50, blank=True)
    gestor = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subordinados',
        verbose_name='Gestor Imediato'
    )
    
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)
    
    class Meta:
        verbose_name = 'Funcionario'
        verbose_name_plural = 'Funcionarios'
        ordering = ['nome']
        unique_together = [['company', 'email'], ['company', 'cpf']]
    
    def __str__(self):
        return f"{self.nome} - {self.cargo} ({self.company.nome_fantasia})"
    
    @property
    def is_active(self):
        """Verifica se o funcionario esta ativo."""
        return self.status == 'ACTIVE'
    
    def get_pending_forms(self):
        """Retorna formularios pendentes de resposta."""
        from forms_builder.models import FormAssignment
        return FormAssignment.objects.filter(
            employee=self,
            status='PENDING',
            form_instance__status='ACTIVE'
        ).select_related('form_instance', 'form_instance__template')
    
    def get_completed_forms(self):
        """Retorna formularios ja respondidos."""
        from forms_builder.models import FormAssignment
        return FormAssignment.objects.filter(
            employee=self,
            status='COMPLETED'
        ).select_related('form_instance', 'form_instance__template')
    
    def create_user_account(self, password=None):
        """
        Cria uma conta de usuario para o funcionario.
        Se password for None, gera uma senha aleatoria.
        """
        from accounts.models import User
        import secrets
        
        if self.user:
            return self.user
        
        if not password:
            password = secrets.token_urlsafe(12)
        
        names = self.nome.split(' ', 1)
        first_name = names[0]
        last_name = names[1] if len(names) > 1 else ''
        
        user = User.objects.create_user(
            email=self.email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            role='EMPLOYEE',
            company=self.company
        )
        
        self.user = user
        self.save(update_fields=['user'])
        
        return user
    
    def deactivate(self, keep_history=True):
        """
        Desativa o funcionario.
        Se keep_history=True, mantem os dados para fins estatisticos.
        """
        self.status = 'TERMINATED'
        if self.user:
            self.user.is_active = False
            self.user.save(update_fields=['is_active'])
        self.save(update_fields=['status', 'updated_at'])

    def get_historical_answers(self):
        """
        Busca o historico completo de respostas vinculadas ao mesmo CPF,
        mesmo que em outras empresas (rastreabilidade SIMDCCONR01).
        """
        if not self.cpf:
            return None
            
        from forms_builder.models import FormAnswer
        return FormAnswer.objects.filter(
            assignment__employee__cpf=self.cpf
        ).exclude(assignment__employee=self).select_related('question', 'assignment__form_instance')


class EmployeeImportLog(models.Model):
    """Registro de importacoes em massa de funcionarios."""
    
    STATUS_CHOICES = [
        ('PENDING', 'Pendente'),
        ('PROCESSING', 'Processando'),
        ('COMPLETED', 'Concluido'),
        ('FAILED', 'Falhou'),
    ]
    
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='import_logs',
        verbose_name='Empresa'
    )
    file_name = models.CharField('Nome do Arquivo', max_length=255)
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
    total_rows = models.IntegerField('Total de Linhas', default=0)
    success_count = models.IntegerField('Importados com Sucesso', default=0)
    error_count = models.IntegerField('Erros', default=0)
    
    errors = models.JSONField('Detalhes dos Erros', default=list, blank=True)
    
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='import_logs',
        verbose_name='Importado por'
    )
    
    class Meta:
        verbose_name = 'Log de Importacao'
        verbose_name_plural = 'Logs de Importacao'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Importacao {self.file_name} - {self.company.nome_fantasia}"
