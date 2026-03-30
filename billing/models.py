"""
Sistema de planos e limites para o SaaS.
Gerencia assinaturas e limites de uso por empresa.
"""
from django.db import models


class Plan(models.Model):
    """Modelo de Plano de assinatura."""
    
    name = models.CharField('Nome do Plano', max_length=100)
    description = models.TextField('Descricao', blank=True)
    
    price_monthly = models.DecimalField('Preco Mensal', max_digits=10, decimal_places=2)
    price_yearly = models.DecimalField('Preco Anual', max_digits=10, decimal_places=2, null=True, blank=True)
    
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
    
    def get_features_list(self):
        """Retorna lista de recursos do plano."""
        features = [
            f"Ate {self.max_employees} funcionarios",
            f"Ate {self.max_forms} formularios ativos",
            f"Ate {self.max_reports} relatorios/mes",
            f"Retencao de dados: {self.data_retention_days} dias",
        ]
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
    
    is_yearly = models.BooleanField('Assinatura Anual', default=False)
    
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Assinatura'
        verbose_name_plural = 'Assinaturas'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.company.nome_fantasia} - {self.plan.name}"
