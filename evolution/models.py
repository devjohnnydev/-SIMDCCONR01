"""
Módulo de Evolução e Inteligência — Comparação histórica automática.
Snapshots, score de risco da empresa e evolução por dimensão.
"""
from django.db import models
from django.utils import timezone


class EvolutionSnapshot(models.Model):
    """
    Foto do estado da empresa em um momento específico.
    Criado automaticamente ao gerar laudos organizacionais.
    """

    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='evolution_snapshots',
        verbose_name='Empresa'
    )
    form_instance = models.ForeignKey(
        'forms_builder.FormInstance',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='evolution_snapshots',
        verbose_name='Formulário de Origem'
    )

    snapshot_date = models.DateField('Data do Snapshot', default=timezone.now)

    overall_score = models.DecimalField(
        'Score Geral (1-5)', max_digits=4, decimal_places=2, default=3.50
    )
    overall_classification = models.CharField(
        'Classificação Geral', max_length=20, default='Adequado'
    )

    # JSONField com scores detalhados
    dimension_scores = models.JSONField(
        'Scores por Dimensão', default=dict, blank=True,
        help_text='{"IMCO|Liderança": 3.5, "FDAC|Fairness": 2.8, ...}'
    )
    sector_scores = models.JSONField(
        'Scores por Setor', default=dict, blank=True,
        help_text='{"Administrativo": 4.1, "Operacional": 2.9, ...}'
    )
    risk_count_by_type = models.JSONField(
        'Riscos por Tipo', default=dict, blank=True,
        help_text='{"critico": 5, "atencao": 12, "adequado": 30, "forte": 10}'
    )

    total_respondentes = models.IntegerField('Total de Respondentes', default=0)
    total_itens_analisados = models.IntegerField('Total de Itens Analisados', default=0)
    pcmso_alertas = models.IntegerField('Alertas PCMSO', default=0)

    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='evolution_snapshots',
        verbose_name='Gerado por'
    )

    class Meta:
        verbose_name = 'Snapshot de Evolução'
        verbose_name_plural = 'Snapshots de Evolução'
        ordering = ['-snapshot_date']
        unique_together = [['company', 'form_instance']]

    def __str__(self):
        return f"Snapshot {self.company.nome_fantasia} — {self.snapshot_date}"

    def compare_with(self, previous):
        """
        Compara este snapshot com um anterior e retorna indicadores.
        Returns: dict com indicadores por dimensão (improved/declined/stable)
        """
        if not previous:
            return {}

        comparison = {}
        for dim, score in self.dimension_scores.items():
            prev_score = previous.dimension_scores.get(dim)
            if prev_score is not None:
                diff = float(score) - float(prev_score)
                if diff > 0.2:
                    trend = 'improved'
                    icon = '🔼'
                elif diff < -0.2:
                    trend = 'declined'
                    icon = '🔽'
                else:
                    trend = 'stable'
                    icon = '➖'
                comparison[dim] = {
                    'current': float(score),
                    'previous': float(prev_score),
                    'diff': round(diff, 2),
                    'trend': trend,
                    'icon': icon,
                }
        return comparison


class RiskScoreHistory(models.Model):
    """
    Histórico de Score de Risco da empresa (0-100).
    0-30 = baixo, 31-70 = médio, 71+ = alto.
    """

    FAIXA_CHOICES = [
        ('BAIXO', 'Baixo Risco (0-30)'),
        ('MEDIO', 'Médio Risco (31-70)'),
        ('ALTO', 'Alto Risco (71+)'),
    ]

    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='risk_score_history',
        verbose_name='Empresa'
    )
    date = models.DateField('Data', default=timezone.now)
    score = models.IntegerField('Score de Risco (0-100)', default=50)
    faixa = models.CharField(
        'Faixa de Risco', max_length=10,
        choices=FAIXA_CHOICES, blank=True
    )

    # Detalhamento por tipo de risco
    score_fisico = models.IntegerField('Score Físico', default=0)
    score_quimico = models.IntegerField('Score Químico', default=0)
    score_biologico = models.IntegerField('Score Biológico', default=0)
    score_ergonomico = models.IntegerField('Score Ergonômico', default=0)
    score_psicossocial = models.IntegerField('Score Psicossocial', default=0)

    created_at = models.DateTimeField('Criado em', auto_now_add=True)

    class Meta:
        verbose_name = 'Histórico de Score de Risco'
        verbose_name_plural = 'Históricos de Score de Risco'
        ordering = ['-date']

    def save(self, *args, **kwargs):
        # Auto-classificar faixa
        if self.score <= 30:
            self.faixa = 'BAIXO'
        elif self.score <= 70:
            self.faixa = 'MEDIO'
        else:
            self.faixa = 'ALTO'
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.company.nome_fantasia} — Score {self.score} ({self.faixa})"


class DimensionEvolution(models.Model):
    """
    Evolução individual de cada dimensão ao longo do tempo.
    Permite gráficos de linha por dimensão.
    """

    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='dimension_evolutions',
        verbose_name='Empresa'
    )
    snapshot = models.ForeignKey(
        EvolutionSnapshot,
        on_delete=models.CASCADE,
        related_name='dimension_details',
        verbose_name='Snapshot'
    )

    instrumento = models.CharField('Instrumento', max_length=20)
    dimensao = models.CharField('Dimensão', max_length=100)
    media = models.DecimalField('Média', max_digits=4, decimal_places=2)
    classificacao = models.CharField('Classificação', max_length=20)
    total_respostas = models.IntegerField('Total de Respostas', default=0)
    date = models.DateField('Data', default=timezone.now)

    class Meta:
        verbose_name = 'Evolução por Dimensão'
        verbose_name_plural = 'Evoluções por Dimensão'
        ordering = ['-date']

    def __str__(self):
        return f"{self.instrumento}|{self.dimensao} = {self.media} ({self.date})"
