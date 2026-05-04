"""
Módulo de Alertas Inteligentes — Notificações proativas do sistema.
Risco alto, prazos, laudos expirando, queda em índices.
"""
from django.db import models
from django.utils import timezone


class Alert(models.Model):
    """
    Alerta inteligente gerado automaticamente ou manualmente.
    """

    TYPE_CHOICES = [
        ('RISK_HIGH', 'Risco Alto Detectado'),
        ('RISK_CRITICAL', 'Risco Crítico Identificado'),
        ('DEADLINE_APPROACHING', 'Prazo Vencendo'),
        ('DEADLINE_OVERDUE', 'Prazo Vencido'),
        ('REPORT_EXPIRING', 'Laudo Expirando'),
        ('HEALTH_DROP', 'Queda no Índice de Saúde'),
        ('SCORE_DECLINE', 'Score de Risco Piorou'),
        ('PAYMENT_DUE', 'Pagamento Pendente'),
        ('FORM_LOW_RESPONSE', 'Baixa Adesão ao Formulário'),
        ('PCMSO_ALERT', 'Alerta PCMSO'),
    ]

    SEVERITY_CHOICES = [
        ('INFO', 'Informação'),
        ('WARNING', 'Atenção'),
        ('CRITICAL', 'Crítico'),
    ]

    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='alerts',
        verbose_name='Empresa'
    )
    target_user = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='alerts',
        verbose_name='Destinatário'
    )

    tipo = models.CharField(
        'Tipo', max_length=30,
        choices=TYPE_CHOICES
    )
    severidade = models.CharField(
        'Severidade', max_length=10,
        choices=SEVERITY_CHOICES, default='WARNING'
    )

    titulo = models.CharField('Título', max_length=300)
    mensagem = models.TextField('Mensagem')

    is_read = models.BooleanField('Lido', default=False)
    is_resolved = models.BooleanField('Resolvido', default=False)
    is_email_sent = models.BooleanField('Email Enviado', default=False)

    # Referência ao objeto relacionado
    related_object_type = models.CharField(
        'Tipo do Objeto', max_length=100, blank=True
    )
    related_object_id = models.IntegerField(
        'ID do Objeto', null=True, blank=True
    )

    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    read_at = models.DateTimeField('Lido em', null=True, blank=True)
    resolved_at = models.DateTimeField('Resolvido em', null=True, blank=True)

    class Meta:
        verbose_name = 'Alerta'
        verbose_name_plural = 'Alertas'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['company', 'is_read']),
            models.Index(fields=['tipo', 'is_resolved']),
        ]

    def __str__(self):
        return f"[{self.get_severidade_display()}] {self.titulo}"

    def mark_read(self):
        self.is_read = True
        self.read_at = timezone.now()
        self.save(update_fields=['is_read', 'read_at'])

    def mark_resolved(self):
        self.is_resolved = True
        self.resolved_at = timezone.now()
        self.save(update_fields=['is_resolved', 'resolved_at'])

    @classmethod
    def unread_count(cls, company):
        """Retorna contagem de alertas não lidos para uma empresa."""
        return cls.objects.filter(company=company, is_read=False).count()

    @classmethod
    def unread_count_for_user(cls, user):
        """Retorna alertas não lidos para um usuário específico."""
        if user.is_admin_master:
            return cls.objects.filter(is_read=False).count()
        if user.company:
            return cls.objects.filter(
                company=user.company, is_read=False
            ).count()
        return 0
