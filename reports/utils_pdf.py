"""
Utilitário de geração de PDF com WeasyPrint puro.
Dependências de sistema (cairo, pango, libgobject) foram adicionadas
ao nixpacks.toml para garantir geração correta no Railway.
"""
import logging

logger = logging.getLogger(__name__)

def html_to_pdf(html_string, base_url=None):
    """
    Converte HTML string em bytes PDF.
    Retorna: (pdf_bytes, error_message)
    """
    import os
    # Patch para ambiente Nixpacks/Railway encontrar as bibliotecas sem quebrar o build global
    lib_path = "/nix/var/nix/profiles/default/lib"
    if os.path.exists(lib_path):
        current_ld = os.environ.get('LD_LIBRARY_PATH', '')
        if lib_path not in current_ld:
            os.environ['LD_LIBRARY_PATH'] = f"{lib_path}:{current_ld}" if current_ld else lib_path

    try:
        from weasyprint import HTML
        if base_url:
            html = HTML(string=html_string, base_url=base_url)
        else:
            html = HTML(string=html_string)
        pdf_bytes = html.write_pdf()
        logger.info("PDF gerado com sucesso via WeasyPrint")
        return pdf_bytes, None
    except ImportError as e:
        logger.error(f"WeasyPrint não está instalado: {str(e)}")
        return None, "Biblioteca de geração de PDF ausente."
    except Exception as e:
        error_str = str(e)
        logger.error(f"Falha no WeasyPrint: {error_str}")
        if 'libgobject' in error_str or 'libcairo' in error_str or 'cannot load library' in error_str:
            return None, "Erro de infraestrutura (dependência de sistema ausente para renderização PDF)."
        return None, f"Erro ao gerar PDF: {error_str}"
