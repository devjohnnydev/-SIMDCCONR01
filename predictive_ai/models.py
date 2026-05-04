"""
Módulo de IA Preditiva e Sugestões Automáticas — NR-01, NR-07, NR-17.
Análise de tendências, previsões de risco e recomendações inteligentes.
"""
from django.db import models
from django.utils import timezone


class PredictiveAlert(models.Model):
    """
    Alerta preditivo gerado pelo motor de IA.
    Detecta tendências negativas antes que se tornem críticas.
    """

    TREND_TYPE_CHOICES = [
        ('SECTOR_DECLINE', 'Setor em Declínio'),
        ('RISK_GROWING', 'Risco Crescente'),
        ('SCORE_PROJECTION', 'Projeção de Score'),
        ('DIMENSION_ALERT', 'Dimensão em Risco'),
        ('EMPLOYEE_PATTERN', 'Padrão Individual'),
    ]

    CONFIDENCE_CHOICES = [
        ('HIGH', 'Alta Confiança'),
        ('MEDIUM', 'Média Confiança'),
        ('LOW', 'Baixa Confiança'),
    ]

    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='predictive_alerts',
        verbose_name='Empresa'
    )

    trend_type = models.CharField(
        'Tipo de Tendência', max_length=30,
        choices=TREND_TYPE_CHOICES
    )
    confidence = models.CharField(
        'Confiança', max_length=10,
        choices=CONFIDENCE_CHOICES, default='MEDIUM'
    )

    titulo = models.CharField('Título', max_length=300)
    descricao = models.TextField('Descrição Detalhada')
    recomendacao = models.TextField('Recomendação Sugerida')

    # Dados da análise
    setor = models.CharField('Setor Afetado', max_length=150, blank=True)
    dimensao = models.CharField('Dimensão Afetada', max_length=150, blank=True)
    score_atual = models.DecimalField(
        'Score Atual', max_digits=5, decimal_places=2, null=True, blank=True
    )
    score_projetado = models.DecimalField(
        'Score Projetado', max_digits=5, decimal_places=2, null=True, blank=True
    )
    data_points = models.JSONField(
        'Dados da Análise', default=list, blank=True,
        help_text='Histórico de scores usados na projeção'
    )

    is_acknowledged = models.BooleanField('Reconhecido', default=False)
    acknowledged_by = models.ForeignKey(
        'accounts.User', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='acknowledged_predictions'
    )
    acknowledged_at = models.DateTimeField('Reconhecido em', null=True, blank=True)

    created_at = models.DateTimeField('Criado em', auto_now_add=True)

    class Meta:
        verbose_name = 'Alerta Preditivo'
        verbose_name_plural = 'Alertas Preditivos'
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.get_confidence_display()}] {self.titulo}"


class NRSuggestion(models.Model):
    """
    Banco de sugestões automáticas vinculadas a NRs.
    Recomendações de medidas de prevenção, ajustes de ambiente e controles.
    """

    RISK_TYPE_CHOICES = [
        ('FISICO', 'Físico'),
        ('QUIMICO', 'Químico'),
        ('BIOLOGICO', 'Biológico'),
        ('ERGONOMICO', 'Ergonômico'),
        ('PSICOSSOCIAL', 'Psicossocial'),
        ('ACIDENTE', 'Acidente / Mecânico'),
    ]

    SEVERITY_CHOICES = [
        ('TRIVIAL', 'Trivial'),
        ('TOLERAVEL', 'Tolerável'),
        ('MODERADO', 'Moderado'),
        ('SUBSTANCIAL', 'Substancial'),
        ('INTOLERAVEL', 'Intolerável'),
    ]

    CATEGORY_CHOICES = [
        ('PREVENCAO', 'Medida de Prevenção'),
        ('AMBIENTE', 'Ajuste de Ambiente'),
        ('EPI', 'EPI Recomendado'),
        ('EPC', 'EPC Recomendado'),
        ('TREINAMENTO', 'Treinamento'),
        ('ORGANIZACIONAL', 'Medida Organizacional'),
        ('ACOMPANHAMENTO', 'Acompanhamento Médico'),
    ]

    tipo_risco = models.CharField(
        'Tipo de Risco', max_length=20,
        choices=RISK_TYPE_CHOICES
    )
    nivel_risco_minimo = models.CharField(
        'Nível Mínimo de Risco', max_length=20,
        choices=SEVERITY_CHOICES, default='MODERADO',
        help_text='Sugestão ativada a partir deste nível'
    )
    norma_referencia = models.CharField(
        'Norma de Referência', max_length=20, default='NR-1',
        help_text='NR-1, NR-7, NR-12, NR-17'
    )

    categoria = models.CharField(
        'Categoria', max_length=20,
        choices=CATEGORY_CHOICES, default='PREVENCAO'
    )
    titulo = models.CharField('Título da Sugestão', max_length=300)
    descricao = models.TextField('Descrição Detalhada')
    fundamentacao = models.TextField(
        'Fundamentação Legal/Teórica', blank=True,
        help_text='Referência ao artigo da NR ou autor teórico'
    )

    prioridade = models.IntegerField(
        'Prioridade de Exibição', default=5,
        help_text='1 = mais prioritária'
    )
    is_active = models.BooleanField('Ativa', default=True)

    created_at = models.DateTimeField('Criado em', auto_now_add=True)

    class Meta:
        verbose_name = 'Sugestão NR'
        verbose_name_plural = 'Sugestões NR'
        ordering = ['prioridade', 'tipo_risco']

    def __str__(self):
        return f"[{self.get_tipo_risco_display()}] {self.titulo}"
