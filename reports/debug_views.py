import sys
import os
import ctypes.util
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from companies.views import require_admin_master

@login_required
@require_admin_master
def system_diagnostics(request):
    """View para diagnosticar bibliotecas ausentes no servidor."""
    
    html = "<h1>Diagnóstico de Sistema (SIMDCCONR01)</h1>"
    
    # 1. Verificar Variáveis de Ambiente
    html += "<h2>Ambiente</h2><ul>"
    for var in ['LD_LIBRARY_PATH', 'PATH', 'PYTHONPATH']:
        html += f"<li><strong>{var}:</strong> {os.environ.get(var, 'N/A')}</li>"
    html += "</ul>"
    
    # 2. Verificar Bibliotecas de Sistema (via ctypes)
    libs_to_check = [
        'gobject-2.0', 'pango-1.0', 'pangocairo-1.0', 'cairo', 'harfbuzz', 'fontconfig'
    ]
    
    html += "<h2>Bibliotecas de Sistema (ctypes lookup)</h2><ul>"
    for lib in libs_to_check:
        found = ctypes.util.find_library(lib)
        status = f"✅ Encontrada: {found}" if found else "❌ NÃO ENCONTRADA"
        html += f"<li><strong>{lib}:</strong> {status}</li>"
    html += "</ul>"
    
    # 3. Testar Importação do WeasyPrint
    html += "<h2>WeasyPrint Status</h2>"
    try:
        from weasyprint import HTML
        import weasyprint
        html += f"<p>✅ Versão: {weasyprint.__version__}</p>"
        html += "<p>Tentando instanciar HTML()...</p>"
        HTML(string="<b>Teste de carga</b>")
        html += "<p>✅ Instanciação bem-sucedida!</p>"
    except Exception as e:
        html += f"<p style='color:red;'>❌ Erro ao carregar WeasyPrint: {str(e)}</p>"
        
    return HttpResponse(html)
