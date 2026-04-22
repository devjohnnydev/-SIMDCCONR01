"""
Utilitário de geração de PDF com xhtml2pdf (pisa).
Substituído WeasyPrint para eliminar dependências de sistema (C libraries).
"""
import logging
import io
from xhtml2pdf import pisa

logger = logging.getLogger(__name__)

def html_to_pdf(html_string, base_url=None):
    """
    Converte HTML string em bytes PDF usando xhtml2pdf.
    Retorna: (pdf_bytes, error_message)
    """
    try:
        # Buffer para o PDF
        result = io.BytesIO()
        
        # O xhtml2pdf converte o HTML diretamente para PDF no buffer
        pisa_status = pisa.CreatePDF(
            io.BytesIO(html_string.encode("UTF-8")),
            dest=result,
            encoding='UTF-8'
        )
        
        if pisa_status.err:
            logger.error(f"Erro no pisa: {pisa_status.err}")
            return None, f"Erro ao renderizar PDF (xhtml2pdf): {pisa_status.err}"
            
        pdf_bytes = result.getvalue()
        result.close()
        
        logger.info("PDF gerado com sucesso via xhtml2pdf")
        return pdf_bytes, None
        
    except Exception as e:
        error_str = str(e)
        logger.error(f"Falha no xhtml2pdf: {error_str}")
        return None, f"Erro inesperado ao gerar PDF: {error_str}"
