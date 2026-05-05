"""
Módulo de Gestão de Documentos — Organização, versionamento e rastreabilidade.
Separação por tipo: Laudos, AET/AEP, PCMSO, PGR.
"""
from django.db import models
from django.utils import timezone


class Document(models.Model):
    """
    Documento regulatório com versionamento automático e rastreabilidade.
    """

    TYPE_CHOICES = [
        ('LAUDO', 'Laudo Pericial'),
        ('AET', 'Análise Ergonômica do Trabalho'),
        ('AEP', 'Avaliação Ergonômica Preliminar'),
        ('PCMSO', 'PCMSO — Programa de Controle Médico'),
        ('PGR', 'PGR — Programa de Gerenciamento de Riscos'),
        ('PPRA', 'PPRA (Legado)'),
        ('LTCAT', 'LTCAT'),
        ('OUTRO', 'Outro'),
    ]

    STATUS_CHOICES = [
        ('DRAFT', 'Rascunho'),
        ('ACTIVE', 'Vigente'),
        ('SUPERSEDED', 'Substituído'),
        ('EXPIRED', 'Expirado'),
    ]

    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='documents',
        verbose_name='Empresa'
    )

    tipo = models.CharField(
        'Tipo de Documento', max_length=20,
        choices=TYPE_CHOICES, default='LAUDO'
    )
    titulo = models.CharField('Título', max_length=300)
    descricao = models.TextField('Descrição', blank=True)

    arquivo = models.FileField(
        'Arquivo', upload_to='documents/%Y/%m/',
        null=True, blank=True
    )
    arquivo_db = models.BinaryField('Arquivo em Banco', null=True, blank=True)
    arquivo_nome = models.CharField('Nome do Arquivo', max_length=255, blank=True, null=True)
    arquivo_mime = models.CharField('MIME Type', max_length=100, blank=True, null=True)


    versao = models.IntegerField('Versão', default=1)
    parent_document = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='child_versions',
        verbose_name='Versão Anterior'
    )

    status = models.CharField(
        'Status', max_length=20,
        choices=STATUS_CHOICES, default='DRAFT'
    )

    # Vinculação com normas
    normas_aplicadas = models.JSONField(
        'Normas Aplicadas', default=list, blank=True,
        help_text='Ex: ["NR-1 (2024.1)", "NR-7 (2024.1)", "NR-17 (2024.1)"]'
    )

    # Datas
    data_emissao = models.DateField('Data de Emissão', null=True, blank=True)
    validade = models.DateField('Validade', null=True, blank=True)

    # Vinculação com relatórios do sistema
    report = models.ForeignKey(
        'reports.Report',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='documents',
        verbose_name='Relatório de Origem'
    )

    # Metadados de autoria
    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='documents_created',
        verbose_name='Criado por'
    )
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'Documento'
        verbose_name_plural = 'Documentos'
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.get_tipo_display()}] {self.titulo} (v{self.versao})"

    def save(self, *args, **kwargs):
        """Sobrescreve save para persistir o arquivo no banco de dados."""
        if self.arquivo:
            try:
                if hasattr(self.arquivo, 'file'):
                    import mimetypes
                    try: self.arquivo.seek(0)
                    except: pass
                    
                    self.arquivo_db = self.arquivo.read()
                    self.arquivo_nome = getattr(self.arquivo, 'name', 'document.pdf').split('/')[-1]
                    self.arquivo_mime = mimetypes.guess_type(self.arquivo_nome)[0] or 'application/pdf'
                    
                    try: self.arquivo.seek(0)
                    except: pass
            except Exception as e:
                print(f"Erro ao persistir arquivo no banco: {e}")
        
        super().save(*args, **kwargs)


    @property
    def is_expired(self):
        if self.validade:
            return self.validade < timezone.now().date()
        return False

    def create_new_version(self, user, arquivo=None):
        """Cria nova versão, marcando a atual como substituída."""
        self.status = 'SUPERSEDED'
        self.save(update_fields=['status', 'updated_at'])

        new_doc = Document(
            company=self.company,
            tipo=self.tipo,
            titulo=self.titulo,
            descricao=self.descricao,
            versao=self.versao + 1,
            parent_document=self,
            status='ACTIVE',
            normas_aplicadas=self.normas_aplicadas,
            data_emissao=timezone.now().date(),
            created_by=user,
        )
        
        if arquivo:
            new_doc.arquivo = arquivo
        else:
            new_doc.arquivo = self.arquivo
            new_doc.arquivo_db = self.arquivo_db
            new_doc.arquivo_nome = self.arquivo_nome
            new_doc.arquivo_mime = self.arquivo_mime
            
        new_doc.save()

        # Registrar no histórico
        DocumentVersion.objects.create(
            document=new_doc,
            versao=new_doc.versao,
            arquivo=new_doc.arquivo,
            arquivo_db=new_doc.arquivo_db,
            arquivo_nome=new_doc.arquivo_nome,
            arquivo_mime=new_doc.arquivo_mime,
            alterado_por=user,
            motivo_alteracao='Nova versão gerada'
        )

        return new_doc


class DocumentVersion(models.Model):
    """
    Histórico de versões de um documento.
    Rastreabilidade: quem alterou e quando.
    """

    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='version_history',
        verbose_name='Documento'
    )
    versao = models.IntegerField('Versão')
    arquivo = models.FileField(
        'Arquivo da Versão', upload_to='documents/versions/%Y/%m/',
        null=True, blank=True
    )
    arquivo_db = models.BinaryField('Arquivo em Banco', null=True, blank=True)
    arquivo_nome = models.CharField('Nome do Arquivo', max_length=255, blank=True, null=True)
    arquivo_mime = models.CharField('MIME Type', max_length=100, blank=True, null=True)

    alterado_por = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='document_versions',
        verbose_name='Alterado por'
    )
    alterado_em = models.DateTimeField('Alterado em', auto_now_add=True)
    motivo_alteracao = models.TextField('Motivo da Alteração', blank=True)

    class Meta:
        verbose_name = 'Versão de Documento'
        verbose_name_plural = 'Versões de Documentos'
        ordering = ['-versao']

    def __str__(self):
        user = self.alterado_por.get_full_name() if self.alterado_por else 'Sistema'
        return f"v{self.versao} — {user} em {self.alterado_em}"

    def save(self, *args, **kwargs):
        """Sobrescreve save para persistir o arquivo no banco de dados."""
        if self.arquivo and not self.arquivo_db:
            try:
                if hasattr(self.arquivo, 'file'):
                    import mimetypes
                    try: self.arquivo.seek(0)
                    except: pass
                    
                    self.arquivo_db = self.arquivo.read()
                    self.arquivo_nome = getattr(self.arquivo, 'name', 'document.pdf').split('/')[-1]
                    self.arquivo_mime = mimetypes.guess_type(self.arquivo_nome)[0] or 'application/pdf'
                    
                    try: self.arquivo.seek(0)
                    except: pass
            except Exception as e:
                print(f"Erro ao persistir arquivo_versao no banco: {e}")
        
        super().save(*args, **kwargs)

