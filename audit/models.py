"""
Sistema de auditoria para rastreabilidade e compliance LGPD.
Registra todas as operacoes importantes no sistema.
"""
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


class AuditLog(models.Model):
    """
    Log de auditoria para rastreabilidade de operacoes.
    Registra quem fez o que, quando e em qual recurso.
    """
    
    ACTION_CHOICES = [
        ('CREATE', 'Criacao'),
        ('UPDATE', 'Atualizacao'),
        ('DELETE', 'Exclusao'),
        ('VIEW', 'Visualizacao'),
        ('EXPORT', 'Exportacao'),
        ('IMPORT', 'Importacao'),
        ('LOGIN', 'Login'),
        ('LOGOUT', 'Logout'),
        ('APPROVE', 'Aprovacao'),
        ('REJECT', 'Rejeicao'),
        ('PUBLISH', 'Publicacao'),
        ('SUBMIT', 'Envio'),
    ]
    
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='audit_logs',
        verbose_name='Usuario'
    )
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs',
        verbose_name='Empresa'
    )
    
    action = models.CharField('Acao', max_length=20, choices=ACTION_CHOICES)
    description = models.TextField('Descricao')
    
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Tipo de Objeto'
    )
    object_id = models.PositiveIntegerField('ID do Objeto', null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    ip_address = models.GenericIPAddressField('Endereco IP', null=True, blank=True)
    user_agent = models.TextField('User Agent', blank=True)
    
    extra_data = models.JSONField('Dados Extras', default=dict, blank=True)
    
    created_at = models.DateTimeField('Data/Hora', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Log de Auditoria'
        verbose_name_plural = 'Logs de Auditoria'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['company', 'created_at']),
            models.Index(fields=['action', 'created_at']),
        ]
    
    def __str__(self):
        user_str = self.user.email if self.user else 'Sistema'
        return f"{user_str} - {self.get_action_display()} - {self.created_at}"
    
    @classmethod
    def log(cls, user, action, description, obj=None, company=None, request=None, extra_data=None):
        """
        Metodo de conveniencia para criar um log de auditoria.
        """
        log_entry = cls(
            user=user,
            action=action,
            description=description,
            company=company or (user.company if user else None),
            extra_data=extra_data or {}
        )
        
        if obj:
            log_entry.content_type = ContentType.objects.get_for_model(obj)
            log_entry.object_id = obj.pk
        
        if request:
            log_entry.ip_address = cls.get_client_ip(request)
            log_entry.user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]
        
        log_entry.save()
        return log_entry
    
    @staticmethod
    def get_client_ip(request):
        """Obtem o IP do cliente da requisicao."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
