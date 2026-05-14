"""
Módulo de Gestão de Riscos Ocupacionais (GRO) — NR-1.
Ciclo completo: Identificar → Avaliar → Controlar → Acompanhar.
"""
from django.db import models
from django.utils import timezone


class HazardRegistry(models.Model):
    """
    Cadastro de Perigos — etapa IDENTIFICAR do GRO.
    Cada perigo é vinculado a setor, função e atividade.
    """

    RISK_TYPE_CHOICES = [
        ('FISICO', 'Físico'),
        ('QUIMICO', 'Químico'),
        ('BIOLOGICO', 'Biológico'),
        ('ERGONOMICO', 'Ergonômico'),
        ('PSICOSSOCIAL', 'Psicossocial'),
        ('ACIDENTE', 'Acidente / Mecânico'),
    ]

    NORM_CHOICES = [
        ('NR-1', 'NR-1 — GRO/PGR'),
        ('NR-7', 'NR-7 — PCMSO'),
        ('NR-12', 'NR-12 — Máquinas'),
        ('NR-17', 'NR-17 — Ergonomia'),
        ('OUTRA', 'Outra'),
    ]

    STATUS_CHOICES = [
        ('PENDING_REVIEW', 'Pendente de Revisão'),
        ('ACTIVE', 'Ativo'),
        ('MITIGATED', 'Mitigado'),
        ('ELIMINATED', 'Eliminado'),
    ]

    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='hazards',
        verbose_name='Empresa'
    )

    setor = models.CharField('Setor / Departamento', max_length=150)
    funcao = models.CharField('Função / Cargo', max_length=150)
    atividade = models.CharField('Atividade', max_length=300)
    descricao_perigo = models.TextField('Descrição do Perigo')
    fonte_geradora = models.CharField('Fonte Geradora', max_length=300, blank=True)

    # Campos para perigos auto-gerados pelo sistema
    auto_generated = models.BooleanField('Gerado Automaticamente', default=False)
    source_dimension = models.CharField(
        'Dimensão de Origem', max_length=100, blank=True,
        help_text='Dimensão do questionário que originou este perigo'
    )
    source_instrument = models.CharField(
        'Instrumento de Origem', max_length=30, blank=True,
        help_text='IMCO, FDAC, NR-01, NR-17, NR-12'
    )
    source_score = models.DecimalField(
        'Score de Origem', max_digits=4, decimal_places=2, null=True, blank=True,
        help_text='Média da dimensão no momento da geração'
    )

    tipo_risco = models.CharField(
        'Tipo de Risco',
        max_length=20,
        choices=RISK_TYPE_CHOICES,
        default='PSICOSSOCIAL'
    )
    norma_referencia = models.CharField(
        'Norma de Referência',
        max_length=10,
        choices=NORM_CHOICES,
        default='NR-1'
    )

    status = models.CharField(
        'Status', max_length=20,
        choices=STATUS_CHOICES, default='ACTIVE'
    )

    # Vínculo opcional com formulário SIMDCCONR01
    form_instance = models.ForeignKey(
        'forms_builder.FormInstance',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='hazards',
        verbose_name='Formulário de Origem'
    )

    identified_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='identified_hazards',
        verbose_name='Identificado por'
    )
    identified_at = models.DateTimeField('Data de Identificação', default=timezone.now)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'Registro de Perigo'
        verbose_name_plural = 'Registros de Perigos'
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.get_tipo_risco_display()}] {self.descricao_perigo[:60]} — {self.setor}"

    @property
    def latest_assessment(self):
        return self.assessments.order_by('-data_avaliacao').first()


class RiskAssessment(models.Model):
    """
    Avaliação de Risco — etapa AVALIAR do GRO.
    Probabilidade × Severidade = Nível de Risco.
    """

    PROBABILITY_CHOICES = [(i, str(i)) for i in range(1, 6)]
    SEVERITY_CHOICES = [(i, str(i)) for i in range(1, 6)]

    RISK_LEVEL_CHOICES = [
        ('TRIVIAL', 'Trivial'),
        ('TOLERAVEL', 'Tolerável'),
        ('MODERADO', 'Moderado'),
        ('SUBSTANCIAL', 'Substancial'),
        ('INTOLERAVEL', 'Intolerável'),
    ]

    hazard = models.ForeignKey(
        HazardRegistry,
        on_delete=models.CASCADE,
        related_name='assessments',
        verbose_name='Perigo'
    )

    probabilidade = models.IntegerField(
        'Probabilidade (1-5)',
        choices=PROBABILITY_CHOICES, default=3
    )
    severidade = models.IntegerField(
        'Severidade (1-5)',
        choices=SEVERITY_CHOICES, default=3
    )

    nivel_risco = models.CharField(
        'Nível de Risco',
        max_length=20,
        choices=RISK_LEVEL_CHOICES,
        blank=True
    )

    score = models.IntegerField('Score (P×S)', default=0)
    justificativa = models.TextField('Justificativa da Avaliação', blank=True)

    avaliado_por = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='risk_assessments',
        verbose_name='Avaliado por'
    )
    data_avaliacao = models.DateField('Data da Avaliação', default=timezone.now)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)

    class Meta:
        verbose_name = 'Avaliação de Risco'
        verbose_name_plural = 'Avaliações de Risco'
        ordering = ['-data_avaliacao']

    def save(self, *args, **kwargs):
        self.score = self.probabilidade * self.severidade
        self.nivel_risco = self._calculate_level()
        super().save(*args, **kwargs)

    def _calculate_level(self):
        """Matriz 5×5 conforme NR-1."""
        s = self.score
        if s <= 2:
            return 'TRIVIAL'
        elif s <= 6:
            return 'TOLERAVEL'
        elif s <= 12:
            return 'MODERADO'
        elif s <= 20:
            return 'SUBSTANCIAL'
        else:
            return 'INTOLERAVEL'

    def __str__(self):
        return f"Avaliação {self.nivel_risco} (P{self.probabilidade}×S{self.severidade}={self.score})"


class ControlMeasure(models.Model):
    """
    Medida de Controle — etapa CONTROLAR do GRO.
    Hierarquia: Eliminação > Substituição > Engenharia > Administrativa > EPI.
    """

    HIERARCHY_CHOICES = [
        ('ELIMINACAO', '1. Eliminação'),
        ('SUBSTITUICAO', '2. Substituição'),
        ('ENGENHARIA', '3. Engenharia'),
        ('ADMINISTRATIVA', '4. Administrativa'),
        ('EPI', '5. EPI'),
        ('EPC', '5. EPC'),
    ]

    risk_assessment = models.ForeignKey(
        RiskAssessment,
        on_delete=models.CASCADE,
        related_name='control_measures',
        verbose_name='Avaliação de Risco'
    )

    tipo = models.CharField(
        'Tipo de Controle',
        max_length=20,
        choices=HIERARCHY_CHOICES,
        default='ADMINISTRATIVA'
    )
    descricao = models.TextField('Descrição da Medida')
    responsavel = models.CharField('Responsável', max_length=200)
    prazo = models.DateField('Prazo de Implementação', null=True, blank=True)
    implementada = models.BooleanField('Implementada?', default=False)
    data_implementacao = models.DateField('Data de Implementação', null=True, blank=True)
    eficacia_verificada = models.BooleanField('Eficácia Verificada?', default=False)
    data_verificacao = models.DateField('Data de Verificação', null=True, blank=True)
    observacoes = models.TextField('Observações', blank=True)

    created_at = models.DateTimeField('Criado em', auto_now_add=True)

    class Meta:
        verbose_name = 'Medida de Controle'
        verbose_name_plural = 'Medidas de Controle'
        ordering = ['tipo']

    def __str__(self):
        return f"[{self.get_tipo_display()}] {self.descricao[:60]}"


class ActionPlan(models.Model):
    """
    Plano de Ação — etapa ACOMPANHAR do GRO.
    Com status de acompanhamento e indicadores de eficácia.
    """

    STATUS_CHOICES = [
        ('PENDENTE', 'Pendente'),
        ('EM_ANDAMENTO', 'Em Andamento'),
        ('CONCLUIDO', 'Concluído'),
        ('CANCELADO', 'Cancelado'),
    ]

    PRIORITY_CHOICES = [
        ('BAIXA', 'Baixa'),
        ('MEDIA', 'Média'),
        ('ALTA', 'Alta'),
        ('URGENTE', 'Urgente'),
    ]

    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='action_plans',
        verbose_name='Empresa'
    )
    risk_assessment = models.ForeignKey(
        RiskAssessment,
        on_delete=models.CASCADE,
        related_name='action_plans',
        verbose_name='Avaliação de Risco',
        null=True, blank=True
    )

    titulo = models.CharField('Título da Ação', max_length=300)
    descricao = models.TextField('Descrição Detalhada')
    responsavel = models.CharField('Responsável', max_length=200)

    prioridade = models.CharField(
        'Prioridade', max_length=20,
        choices=PRIORITY_CHOICES, default='MEDIA'
    )
    status = models.CharField(
        'Status', max_length=20,
        choices=STATUS_CHOICES, default='PENDENTE'
    )

    prazo_inicio = models.DateField('Prazo de Início', null=True, blank=True)
    prazo_fim = models.DateField('Prazo de Conclusão')
    data_conclusao = models.DateField('Data de Conclusão Efetiva', null=True, blank=True)

    indicador_eficacia = models.TextField(
        'Indicador de Eficácia', blank=True,
        help_text='Como a eficácia será medida (ex: reaplicação SIMDCCONR01)'
    )
    percentual_conclusao = models.IntegerField('% Conclusão', default=0)

    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='action_plans_created',
        verbose_name='Criado por'
    )
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'Plano de Ação'
        verbose_name_plural = 'Planos de Ação'
        ordering = ['-prazo_fim']

    def __str__(self):
        return f"[{self.get_status_display()}] {self.titulo[:60]}"

    @property
    def is_overdue(self):
        """Verifica se o prazo foi ultrapassado."""
        if self.status in ('CONCLUIDO', 'CANCELADO'):
            return False
        return self.prazo_fim < timezone.now().date()
