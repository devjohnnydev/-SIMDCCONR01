"""
Modelo de Usuario customizado com roles para o SaaS NR-01.
Suporta autenticacao por email e tres tipos de usuarios:
ADMIN_MASTER, COMPANY_ADMIN e EMPLOYEE.
"""
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    """Gerenciador customizado para o modelo User."""
    
    def create_user(self, email, password=None, **extra_fields):
        """Cria e salva um usuario comum."""
        if not email:
            raise ValueError('O email e obrigatorio')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        """Cria e salva um superusuario (ADMIN_MASTER)."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'ADMIN_MASTER')
        extra_fields.setdefault('is_active', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser precisa ter is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser precisa ter is_superuser=True.')
        
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Modelo de usuario customizado usando email como username.
    Implementa sistema de roles para controle de acesso.
    """
    
    ROLE_CHOICES = [
        ('ADMIN_MASTER', 'Administrador Master'),
        ('COMPANY_ADMIN', 'Administrador da Empresa'),
        ('EMPLOYEE', 'Funcionario'),
    ]
    
    email = models.EmailField('Email', unique=True)
    first_name = models.CharField('Nome', max_length=150)
    last_name = models.CharField('Sobrenome', max_length=150)
    role = models.CharField('Papel', max_length=20, choices=ROLE_CHOICES, default='EMPLOYEE')
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='users',
        verbose_name='Empresa'
    )
    
    is_active = models.BooleanField('Ativo', default=True)
    is_staff = models.BooleanField('Acesso ao Admin', default=False)
    # LGPD - Consentimento Duplo SIMDCCONR01
    lgpd_individual_accepted = models.BooleanField('Consentimento Individual (Analise)', default=False)
    lgpd_individual_at = models.DateTimeField('Data Consentimento Individual', null=True, blank=True)
    
    lgpd_aggregate_accepted = models.BooleanField('Consentimento Agregado (PGR/GRO)', default=False)
    lgpd_aggregate_at = models.DateTimeField('Data Consentimento Agregado', null=True, blank=True)
    
    terms_accepted = models.BooleanField('Termos Aceitos', default=False)
    terms_accepted_at = models.DateTimeField('Data Aceite Termos', null=True, blank=True)
    privacy_accepted = models.BooleanField('Privacidade Aceita', default=False)
    privacy_accepted_at = models.DateTimeField('Data Aceite Privacidade', null=True, blank=True)
    
    date_joined = models.DateTimeField('Data de Cadastro', default=timezone.now)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        ordering = ['-date_joined']
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"
    
    def get_full_name(self):
        """Retorna o nome completo do usuario."""
        return f"{self.first_name} {self.last_name}".strip()
    
    def get_short_name(self):
        """Retorna o primeiro nome do usuario."""
        return self.first_name
    
    @property
    def is_admin_master(self):
        """Verifica se e ADMIN_MASTER."""
        return self.role == 'ADMIN_MASTER'
    
    @property
    def is_company_admin(self):
        """Verifica se e COMPANY_ADMIN."""
        return self.role == 'COMPANY_ADMIN'
    
    @property
    def is_employee(self):
        """Verifica se e EMPLOYEE."""
        return self.role == 'EMPLOYEE'
    
    def accept_terms(self):
        """Registra aceite dos termos de uso."""
        self.terms_accepted = True
        self.terms_accepted_at = timezone.now()
        self.save(update_fields=['terms_accepted', 'terms_accepted_at'])
    
    def accept_privacy(self):
        """Registra aceite da politica de privacidade."""
        self.privacy_accepted = True
        self.privacy_accepted_at = timezone.now()
        self.save(update_fields=['privacy_accepted', 'privacy_accepted_at'])
