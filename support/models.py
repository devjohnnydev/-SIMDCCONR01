from django.db import models
from django.conf import settings

class Ticket(models.Model):
    """Agrupa mensagens de suporte entre uma empresa e os administradores master."""
    
    STATUS_CHOICES = [
        ('OPEN', 'Aberto'),
        ('IN_PROGRESS', 'Em Atendimento'),
        ('CLOSED', 'Fechado'),
    ]
    
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='support_tickets',
        verbose_name='Empresa'
    )
    subject = models.CharField('Assunto', max_length=200)
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default='OPEN')
    
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)
    
    class Meta:
        verbose_name = 'Ticket de Suporte'
        verbose_name_plural = 'Tickets de Suporte'
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"{self.subject} - {self.company.nome_fantasia}"


class Message(models.Model):
    """Mensagem individual dentro de um ticket de suporte."""
    
    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name='Ticket'
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='support_messages',
        verbose_name='Remetente'
    )
    content = models.TextField('Mensagem')
    is_read = models.BooleanField('Lida', default=False)
    
    created_at = models.DateTimeField('Enviada em', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Mensagem de Suporte'
        verbose_name_plural = 'Mensagens de Suporte'
        ordering = ['created_at']
    
    def __str__(self):
        return f"Mensagem de {self.sender.get_full_name()} em {self.created_at}"
