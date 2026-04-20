"""
Modelo de Empresa (Company) para o sistema multi-tenant.
Cada empresa representa um tenant no sistema.
"""
from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone


class Company(models.Model):
    """
    Modelo principal de Empresa/Tenant.
    Armazena dados cadastrais, personalizacao visual e configuracoes.
    """
    
    STATUS_CHOICES = [
        ('PENDING', 'Aguardando Aprovacao'),
        ('ACTIVE', 'Ativa'),
        ('SUSPENDED', 'Suspensa'),
        ('CANCELLED', 'Cancelada'),
    ]
    
    cnpj_validator = RegexValidator(
        regex=r'^\d{14}$',
        message='CNPJ deve conter 14 digitos numericos'
    )
    
    phone_validator = RegexValidator(
        regex=r'^\d{10,11}$',
        message='Telefone deve conter 10 ou 11 digitos'
    )
    
    nome_fantasia = models.CharField('Nome Fantasia', max_length=200)
    razao_social = models.CharField('Razao Social', max_length=200)
    cnpj = models.CharField('CNPJ', max_length=14, unique=True, validators=[cnpj_validator])
    
    responsavel_nome = models.CharField('Nome do Responsavel', max_length=200)
    responsavel_email = models.EmailField('Email do Responsavel')
    telefone = models.CharField('Telefone', max_length=11, validators=[phone_validator])
    
    endereco = models.CharField('Endereco', max_length=300, blank=True)
    cidade = models.CharField('Cidade', max_length=100, blank=True)
    estado = models.CharField('Estado', max_length=2, blank=True)
    cep = models.CharField('CEP', max_length=8, blank=True)
    
    # Contrato SaaS SIMDCCONR01
    contratante_nome = models.CharField('Nome do Contratante', max_length=200, blank=True, null=True)
    contratante_documento = models.CharField('CPF do Contratante', max_length=20, blank=True, null=True)
    data_aceite_contrato = models.DateTimeField('Data e Hora de Assinatura', blank=True, null=True)
    
    
    logo = models.ImageField('Logo', upload_to='logos/', null=True, blank=True)
    cor_primaria = models.CharField('Cor Primaria', max_length=7, default='#0d6efd')
    cor_secundaria = models.CharField('Cor Secundaria', max_length=7, default='#6c757d')
    
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
    plan = models.ForeignKey(
        'billing.Plan',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='companies',
        verbose_name='Plano'
    )
    
    # Custom Pricing (Overrides Plan default if set)
    custom_price_monthly = models.DecimalField('Preco Mensal Customizado', max_digits=10, decimal_places=2, null=True, blank=True)
    custom_price_yearly = models.DecimalField('Preco Anual Customizado', max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Stripe Integration
    stripe_customer_id = models.CharField('ID Cliente Stripe', max_length=100, blank=True)
    stripe_subscription_id = models.CharField('ID Assinatura Stripe', max_length=100, blank=True)
    subscription_status = models.CharField('Status Assinatura', max_length=50, default='inactive')
    current_period_end = models.DateTimeField('Fim do Periodo Atual', null=True, blank=True)
    
    configs = models.JSONField('Configuracoes', default=dict, blank=True)
    
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)
    approved_at = models.DateTimeField('Aprovado em', null=True, blank=True)
    approved_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_companies',
        verbose_name='Aprovado por'
    )
    
    class Meta:
        verbose_name = 'Empresa'
        verbose_name_plural = 'Empresas'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.nome_fantasia
    
    def approve(self, user):
        """Aprova a empresa e registra quem aprovou."""
        self.status = 'ACTIVE'
        self.approved_at = timezone.now()
        self.approved_by = user
        self.save()
    
    def suspend(self):
        """Suspende a empresa."""
        self.status = 'SUSPENDED'
        self.save(update_fields=['status', 'updated_at'])
    
    def reactivate(self):
        """Reativa uma empresa suspensa."""
        self.status = 'ACTIVE'
        self.save(update_fields=['status', 'updated_at'])
    
    @property
    def is_active(self):
        """Verifica se a empresa esta ativa conforme status e assinatura."""
        return self.status == 'ACTIVE' and self.subscription_status in ['active', 'trialing']
    
    def get_price_monthly(self):
        """Retorna o preco mensal efetivo (customizado ou do plano)."""
        if self.custom_price_monthly:
            return self.custom_price_monthly
        if self.plan:
            return self.plan.price_monthly
        return 0
    
    def get_price_yearly(self):
        """Retorna o preco anual efetivo (customizado ou do plano)."""
        if self.custom_price_yearly:
            return self.custom_price_yearly
        if self.plan:
            return self.plan.price_yearly
        return 0
    
    @property
    def is_pending(self):
        """Verifica se a empresa esta aguardando aprovacao."""
        return self.status == 'PENDING'
    
    def get_employee_count(self):
        """Retorna o numero de funcionarios ativos."""
        return self.employees.filter(status='ACTIVE').count()
    
    def get_active_forms_count(self):
        """Retorna o numero de formularios ativos."""
        return self.form_instances.filter(status='ACTIVE').count()
    
    def can_add_employee(self):
        """Verifica se pode adicionar mais funcionarios baseado no plano."""
        if not self.plan:
            return False
        return self.get_employee_count() < self.plan.max_employees
    
    def can_add_form(self):
        """Verifica se pode criar mais formularios baseado no plano."""
        if not self.plan:
            return False
        return self.get_active_forms_count() < self.plan.max_forms

    @property
    def has_active_plan(self):
        """Verifica se a empresa possui um plano ativo e dentro do período."""
        return (
            self.plan is not None
            and self.subscription_status in ('active', 'trialing')
        )


class Announcement(models.Model):
    """Comunicados e avisos da empresa para funcionarios."""
    
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='announcements',
        verbose_name='Empresa'
    )
    title = models.CharField('Titulo', max_length=200)
    content = models.TextField('Conteudo')
    is_active = models.BooleanField('Ativo', default=True)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='announcements',
        verbose_name='Criado por'
    )
    
    class Meta:
        verbose_name = 'Comunicado'
        verbose_name_plural = 'Comunicados'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.company.nome_fantasia}"
