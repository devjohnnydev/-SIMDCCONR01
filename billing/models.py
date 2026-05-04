"""
Sistema de planos e limites para o SaaS.
Gerencia assinaturas e limites de uso por empresa.
"""
from django.db import models


class Plan(models.Model):
    """Modelo de Plano de assinatura com pricing dinâmico."""

    PRICING_MODE_CHOICES = [
        ('FIXED', 'Preço Fixo'),
        ('DYNAMIC', 'Base + Por Funcionário'),
    ]

    BILLING_CYCLE_CHOICES = [
        ('MONTHLY', 'Mensal'),
        ('SEMESTRAL', 'Semestral'),
    ]
    
    name = models.CharField('Nome do Plano', max_length=100)
    description = models.TextField('Descricao', blank=True)
    
    # Pricing fixo (legado / compatível)
    price_monthly = models.DecimalField('Preco Mensal', max_digits=10, decimal_places=2)
    price_yearly = models.DecimalField('Preco Anual', max_digits=10, decimal_places=2, null=True, blank=True)
    price_semestral = models.DecimalField('Preço Semestral', max_digits=10, decimal_places=2, null=True, blank=True)

    # Pricing dinâmico (Base + por funcionário)
    pricing_mode = models.CharField(
        'Modo de Pricing', max_length=10,
        choices=PRICING_MODE_CHOICES, default='FIXED'
    )
    base_price = models.DecimalField(
        'Preço Base (R$)', max_digits=10, decimal_places=2,
        default=99, help_text='Valor base do plano'
    )
    per_employee_price = models.DecimalField(
        'Valor por Funcionário (R$)', max_digits=8, decimal_places=2,
        default=10, help_text='Valor adicional por funcionário'
    )

    # Regras de desconto progressivo
    min_employees_discount = models.IntegerField(
        'Mín. Func. Desconto', default=6,
        help_text='A partir de quantos funcionários aplica desconto'
    )
    discount_pct_small = models.DecimalField(
        'Desconto 6-20 func. (%)', max_digits=5, decimal_places=2,
        default=5, help_text='Percentual de desconto para 6-20 funcionários'
    )
    discount_pct_corporate = models.DecimalField(
        'Desconto 20+ func. (%)', max_digits=5, decimal_places=2,
        default=15, help_text='Percentual de desconto para 20+ funcionários'
    )

    # Ciclo de cobrança padrão
    default_billing_cycle = models.CharField(
        'Ciclo Padrão', max_length=10,
        choices=BILLING_CYCLE_CHOICES, default='SEMESTRAL'
    )

    max_employees = models.IntegerField('Limite de Funcionarios', default=50)
    max_forms = models.IntegerField('Limite de Formularios Ativos', default=10)
    max_reports = models.IntegerField('Relatorios por Mes', default=20)
    
    data_retention_days = models.IntegerField('Retencao de Dados (dias)', default=365)
    
    has_pdf_export = models.BooleanField('Exportacao PDF', default=True)
    has_csv_import = models.BooleanField('Importacao CSV', default=True)
    has_api_access = models.BooleanField('Acesso API', default=False)
    has_custom_branding = models.BooleanField('Personalizacao Visual', default=True)
    has_priority_support = models.BooleanField('Suporte Prioritario', default=False)
    
    is_active = models.BooleanField('Ativo', default=True)
    is_featured = models.BooleanField('Destaque', default=False)
    
    order = models.PositiveIntegerField('Ordem de Exibicao', default=0)
    
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)
    
    class Meta:
        verbose_name = 'Plano'
        verbose_name_plural = 'Planos'
        ordering = ['order', 'price_monthly']
    
    def __str__(self):
        return f"{self.name} - R$ {self.price_monthly}/mes"
    
    def calculate_dynamic_price(self, num_employees):
        """
        Calcula preço dinâmico baseado no número de funcionários.
        Regras:
          - Até 5 func. → preço mínimo (base_price)
          - 6-20 func. → base + (func × per_employee) - desconto progressivo
          - 20+ func. → base + (func × per_employee) - desconto corporativo
        """
        from decimal import Decimal

        if self.pricing_mode == 'FIXED':
            return self.price_monthly

        total = self.base_price + (Decimal(num_employees) * self.per_employee_price)

        if num_employees <= 5:
            # Plano mínimo — sem desconto
            pass
        elif num_employees <= 20:
            # Desconto progressivo pequeno
            total = total * (1 - self.discount_pct_small / 100)
        else:
            # Desconto corporativo
            total = total * (1 - self.discount_pct_corporate / 100)

        return round(total, 2)

    def calculate_semestral_price(self, num_employees):
        """Calcula preço semestral (6 × mensal com desconto)."""
        monthly = self.calculate_dynamic_price(num_employees)
        # Desconto de 10% no semestral
        return round(monthly * 6 * Decimal('0.90'), 2)

    def get_tier_label(self, num_employees):
        """Retorna label do tier baseado em funcionários."""
        if num_employees <= 5:
            return 'Plano Mínimo'
        elif num_employees <= 20:
            return 'Plano Progressivo'
        return 'Plano Corporativo'

    def get_features_list(self):
        """Retorna lista de recursos do plano."""
        features = [
            f"Ate {self.max_employees} funcionarios",
            f"Ate {self.max_forms} formularios ativos",
            f"Ate {self.max_reports} relatorios/mes",
            f"Retencao de dados: {self.data_retention_days} dias",
        ]
        if self.pricing_mode == 'DYNAMIC':
            features.insert(0, f"Base R$ {self.base_price} + R$ {self.per_employee_price}/func.")
        if self.has_pdf_export:
            features.append("Exportacao em PDF")
        if self.has_csv_import:
            features.append("Importacao via CSV")
        if self.has_api_access:
            features.append("Acesso a API")
        if self.has_custom_branding:
            features.append("Personalizacao visual")
        if self.has_priority_support:
            features.append("Suporte prioritario")
        return features


class Subscription(models.Model):
    """Historico de assinaturas de uma empresa."""
    
    STATUS_CHOICES = [
        ('ACTIVE', 'Ativa'),
        ('CANCELLED', 'Cancelada'),
        ('EXPIRED', 'Expirada'),
        ('SUSPENDED', 'Suspensa'),
    ]
    
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name='Empresa'
    )
    plan = models.ForeignKey(
        Plan,
        on_delete=models.PROTECT,
        related_name='subscriptions',
        verbose_name='Plano'
    )
    
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    
    start_date = models.DateField('Data de Inicio')
    end_date = models.DateField('Data de Termino', null=True, blank=True)
    
    BILLING_CYCLE_CHOICES = [
        ('MONTHLY', 'Mensal'),
        ('SEMESTRAL', 'Semestral'),
        ('YEARLY', 'Anual'),
    ]

    is_yearly = models.BooleanField('Assinatura Anual', default=False)
    billing_cycle = models.CharField(
        'Ciclo de Cobrança', max_length=10,
        choices=BILLING_CYCLE_CHOICES, default='SEMESTRAL'
    )
    employee_count_at_subscription = models.IntegerField(
        'Func. na Contratação', default=0,
        help_text='Número de funcionários no momento da assinatura'
    )
    calculated_price = models.DecimalField(
        'Preço Calculado', max_digits=10, decimal_places=2,
        null=True, blank=True,
        help_text='Preço calculado com base no número de funcionários'
    )
    
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Assinatura'
        verbose_name_plural = 'Assinaturas'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.company.nome_fantasia} - {self.plan.name}"


class PaymentOrder(models.Model):
    """Registro de pagamento via Stripe Checkout."""

    STATUS_CHOICES = [
        ('pending', 'Aguardando Pagamento'),
        ('paid', 'Pago'),
        ('failed', 'Falhou'),
        ('cancelled', 'Cancelado'),
    ]

    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='payment_orders',
        verbose_name='Empresa'
    )
    plan = models.ForeignKey(
        Plan,
        on_delete=models.PROTECT,
        related_name='payment_orders',
        verbose_name='Plano'
    )

    is_yearly = models.BooleanField('Assinatura Anual', default=False)
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default='pending')

    amount = models.IntegerField('Valor (centavos)', default=0,
                                  help_text='Valor em centavos BRL')

    stripe_session_id = models.CharField('Stripe Session ID', max_length=255, blank=True, db_index=True)
    stripe_payment_intent_id = models.CharField('Stripe Payment Intent ID', max_length=255, blank=True)

    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    paid_at = models.DateTimeField('Pago em', null=True, blank=True)

    class Meta:
        verbose_name = 'Ordem de Pagamento'
        verbose_name_plural = 'Ordens de Pagamento'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['stripe_session_id']),
        ]

    def __str__(self):
        return f"Order #{self.id} - {self.company.nome_fantasia} - {self.get_status_display()}"


class CustomPlanRequest(models.Model):
    """Solicitações de planos personalizados pelas empresas."""

    STATUS_CHOICES = [
        ('pending', 'Pendente de Análise'),
        ('proposed', 'Proposta Enviada'),
        ('accepted', 'Aceita / Assinada'),
        ('rejected', 'Recusada / Cancelada'),
    ]

    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='custom_plan_requests',
        verbose_name='Empresa'
    )
    
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default='pending')

    # Features desejadas
    max_employees = models.IntegerField('Limite de Funcionários', default=50)
    max_forms = models.IntegerField('Limite de Formulários Ativos', default=10)
    max_reports = models.IntegerField('Relatórios por Mês', default=20)
    data_retention_days = models.IntegerField('Retenção de Dados (dias)', default=365)
    
    has_pdf_export = models.BooleanField('Exportação PDF', default=True)
    has_csv_import = models.BooleanField('Importação CSV', default=True)
    has_api_access = models.BooleanField('Acesso API', default=False)
    has_custom_branding = models.BooleanField('Personalização Visual', default=True)
    has_priority_support = models.BooleanField('Suporte Prioritário', default=False)

    # Valores propostos pelo admin
    proposed_price_monthly = models.DecimalField('Preço Mensal Proposto', max_digits=10, decimal_places=2, null=True, blank=True)
    proposed_price_yearly = models.DecimalField('Preço Anual Proposto', max_digits=10, decimal_places=2, null=True, blank=True)
    
    admin_message = models.TextField('Mensagem do Admin', blank=True)
    user_message = models.TextField('Mensagem da Empresa', blank=True, help_text="Usado em contrapropostas ou justificativas")

    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'Solicitação de Plano Personalizado'
        verbose_name_plural = 'Solicitações de Planos Personalizados'
        ordering = ['-created_at']

    def __str__(self):
        return f"Solicitação - {self.company.nome_fantasia} ({self.get_status_display()})"

