from django.db import models
from django.utils import timezone
from django.db.utils import ProgrammingError
from django.core.management import call_command


class LandingConfig(models.Model):
    """
    Configuração singleton da Landing Page.
    Editável pelo Admin Master via painel de gerenciamento.
    """
    # --- Cores ---
    primary_color   = models.CharField('Cor Primária',   max_length=7, default='#2563EB')
    secondary_color = models.CharField('Cor Secundária', max_length=7, default='#0D9488')
    accent_color    = models.CharField('Cor Destaque',   max_length=7, default='#7C3AED')
    dark_bg_color   = models.CharField('Fundo Escuro',   max_length=7, default='#0A0F1E')

    # --- Hero ---
    hero_badge     = models.CharField('Badge do Hero', max_length=200,
                                      default='Nova Obrigação Legal — NR-1 / Portaria MTE 1.419/2024')
    hero_title1    = models.CharField('Título Linha 1', max_length=200, default='Saúde Mental no Trabalho')
    hero_title2    = models.CharField('Título Linha 2', max_length=200, default='não é opcional.')
    hero_highlight = models.CharField('Título Destaque', max_length=200, default='É lei. É urgente.')
    hero_subtitle  = models.TextField('Subtítulo do Hero',
                                      default='O sistema mais completo do Brasil para diagnóstico de riscos psicossociais, compliance NR-1, NR-17 e NR-12 — com 160 questões validadas e inteligência artificial.')
    ticker_text    = models.TextField('Texto do Ticker (Faixa Superior)', 
                                      default='Condição Especial: Desconto Exclusivo nos Planos | Acesso Imediato | SIMDCCONR01 — Líder em Riscos Psicossociais')
    hero_cta_text  = models.CharField('Texto CTA Hero', max_length=100, default='Proteja sua Empresa Agora')
    hero_image     = models.ImageField('Imagem de Fundo', upload_to='landing/', null=True, blank=True)

    # --- Planos ---
    starter_price       = models.DecimalField('Preço Starter',        max_digits=8, decimal_places=2, default=420)
    starter_employees   = models.IntegerField('Max Func. Starter',    default=50)
    starter_description = models.CharField('Descrição Starter',       max_length=200, default='Para PMEs até 50 colaboradores')

    pro_price       = models.DecimalField('Preço Professional',   max_digits=8, decimal_places=2, default=2250)
    pro_employees   = models.IntegerField('Max Func. Professional', default=300)
    pro_description = models.CharField('Descrição Professional',  max_length=200, default='Para empresas de 50 a 300 colaboradores')

    enterprise_description = models.CharField('Descrição Enterprise', max_length=200, default='Para grupos e conglomerados +300')
    enterprise_contact     = models.EmailField('Email Enterprise',     default='contato@simdcconr01.com.br')

    # --- CTA Final ---
    cta_title    = models.CharField('Título CTA Final', max_length=200, default='Sua empresa está pronta para a nova NR-1?')
    cta_subtitle = models.TextField('Subtítulo CTA Final',
                                    default='Evite multas, proteja sua equipe e mantenha o PGR atualizado. Comece hoje com o sistema mais completo do Brasil.')

    # --- Contato / SEO ---
    contact_email    = models.EmailField('Email de Contato', default='contato@simdcconr01.com.br')
    meta_description = models.TextField('Meta Description SEO', max_length=300,
                                        default='O sistema mais completo do Brasil para diagnóstico de riscos psicossociais, compliance NR-1, NR-17 e NR-12.')

    updated_at = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'Configuração da Landing Page'

    def __str__(self):
        return 'Configuração da Landing Page'

    @classmethod
    def get(cls):
        try:
            obj, _ = cls.objects.get_or_create(pk=1)
            return obj
        except ProgrammingError:
            print("AVISO: Tabela landing ausente. Forçando migração em tempo real (runtime)...")
            call_command('makemigrations', 'landing', interactive=False)
            call_command('migrate', 'landing', interactive=False)
            obj, _ = cls.objects.get_or_create(pk=1)
            return obj


class Testimonial(models.Model):
    """Depoimentos/comentários submetidos para aprovação."""
    author_name    = models.CharField('Nome do Autor', max_length=100)
    author_role    = models.CharField('Cargo',         max_length=100, blank=True)
    author_company = models.CharField('Empresa',       max_length=100, blank=True)
    content        = models.TextField('Depoimento')
    rating         = models.IntegerField('Nota (1-5)',  default=5)
    avatar         = models.ImageField('Foto',          upload_to='testimonials/', null=True, blank=True)
    is_approved    = models.BooleanField('Aprovado',    default=False)
    created_at     = models.DateTimeField('Enviado em', auto_now_add=True)

    class Meta:
        verbose_name = 'Depoimento'
        verbose_name_plural = 'Depoimentos'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.author_name} — {"✅" if self.is_approved else "⏳"}'


class Announcement(models.Model):
    """Informações importantes para exibir na landing page."""
    TYPE_CHOICES = [
        ('INFO',    'Informação'),
        ('WARNING', 'Alerta'),
        ('SUCCESS', 'Destaque positivo'),
        ('PROMO',   'Promoção'),
    ]
    title            = models.CharField('Título',    max_length=200)
    content          = models.TextField('Conteúdo')
    announcement_type = models.CharField('Tipo', max_length=20, choices=TYPE_CHOICES, default='INFO')
    is_active        = models.BooleanField('Ativo',     default=True)
    expires_at       = models.DateTimeField('Expira em', null=True, blank=True)
    created_at       = models.DateTimeField('Criado em', auto_now_add=True)
    created_by       = models.ForeignKey(
        'accounts.User', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Criado por'
    )

    class Meta:
        verbose_name = 'Aviso'
        verbose_name_plural = 'Avisos'
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    @property
    def is_live(self):
        if not self.is_active:
            return False
        if self.expires_at and self.expires_at < timezone.now():
            return False
        return True
