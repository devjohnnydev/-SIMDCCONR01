"""
==================================================================================
REPORTS SERVICES — Arquivamento e Notificações
==================================================================================
Serviços para salvar PDFs gerados nos Documentos da empresa e
notificar quando relatórios estão prontos.
==================================================================================
"""
import logging
from django.utils import timezone
from django.utils.text import slugify

logger = logging.getLogger(__name__)


def archive_report_to_documents(pdf_bytes, company, titulo, user=None,
                                 normas=None, form_instance=None):
    """
    Salva um PDF gerado como Document na empresa.
    
    Args:
        pdf_bytes: bytes do PDF.
        company: Company instance.
        titulo: Título do documento.
        user: User que gerou.
        normas: lista de normas aplicadas (default NR-01/17/12).
        form_instance: FormInstance de origem (opcional).
    
    Returns:
        Document instance criada.
    """
    from documents.models import Document
    
    if normas is None:
        normas = ['NR-01', 'NR-17', 'NR-12']
    
    doc = Document.objects.create(
        company=company,
        tipo='LAUDO',
        titulo=titulo,
        status='ACTIVE',
        data_emissao=timezone.now().date(),
        created_by=user,
        arquivo_db=pdf_bytes,
        arquivo_nome=f"{slugify(titulo)}.pdf",
        arquivo_mime='application/pdf',
        normas_aplicadas=normas,
    )
    
    logger.info(f"Relatório arquivado: {titulo} (Doc ID: {doc.pk}) — {company.nome_fantasia}")
    return doc


def notify_company_report_ready(company, report_title, document=None):
    """
    Cria alerta para a empresa informando que um relatório está disponível.
    
    Args:
        company: Company instance.
        report_title: título do relatório.
        document: Document instance (opcional, para link direto).
    """
    from alerts.models import Alert
    
    Alert.objects.create(
        company=company,
        tipo='REPORT_GENERATED',
        severidade='INFO',
        titulo=f'Novo relatório disponível: {report_title}',
        mensagem=(
            f'O relatório "{report_title}" foi gerado pelo sistema SIMDCCONR01 '
            f'e está disponível nos Documentos da empresa para consulta e download.'
        ),
    )
    
    logger.info(f"Notificação enviada: {report_title} — {company.nome_fantasia}")
