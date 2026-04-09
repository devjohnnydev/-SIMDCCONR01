"""
URL configuration for SaaS NR-01 project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from decouple import config
from django.views.generic import TemplateView
from django.http import JsonResponse
import json, urllib.request

def cnpj_lookup(request, cnpj):
    """Proxy para APIs gratuitas de consulta de CNPJ."""
    cnpj_clean = ''.join(filter(str.isdigit, cnpj))
    if len(cnpj_clean) != 14:
        return JsonResponse({'error': 'CNPJ inválido'}, status=400)

    apis = [
        f'https://brasilapi.com.br/api/cnpj/v1/{cnpj_clean}',
        f'https://publica.cnpj.ws/cnpj/{cnpj_clean}',
        f'https://www.receitaws.com.br/v1/cnpj/{cnpj_clean}',
    ]

    for url in apis:
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'SIMDCCONR01/1.0'})
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read())
                # Normaliza campos entre APIs
                return JsonResponse({
                    'razao_social':   data.get('razao_social') or data.get('nome') or '',
                    'nome_fantasia':  data.get('nome_fantasia') or '',
                    'logradouro':     data.get('logradouro') or (data.get('endereco', {}) or {}).get('logradouro', ''),
                    'numero':         data.get('numero') or (data.get('endereco', {}) or {}).get('numero', ''),
                    'complemento':    data.get('complemento') or '',
                    'bairro':         data.get('bairro') or (data.get('endereco', {}) or {}).get('bairro', ''),
                    'municipio':      data.get('municipio') or (data.get('endereco', {}) or {}).get('municipio', ''),
                    'uf':             data.get('uf') or (data.get('endereco', {}) or {}).get('uf', ''),
                    'cep':            data.get('cep') or (data.get('endereco', {}) or {}).get('cep', ''),
                    'email':          data.get('email') or '',
                    'telefone':       data.get('telefone') or data.get('ddd_telefone_1') or '',
                    'situacao':       data.get('situacao') or data.get('descricao_situacao_cadastral') or '',
                    'atividade':      (data.get('cnae_fiscal_descricao') or
                                      (data.get('atividade_principal', [{}]) or [{}])[0].get('text', '')),
                    'source': url.split('/')[2],
                })
        except Exception:
            continue

    return JsonResponse({'error': 'Não foi possível consultar o CNPJ. Tente novamente.'}, status=503)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('landing.urls')),
    path('accounts/', include('accounts.urls')),
    path('companies/', include('companies.urls')),
    path('employees/', include('employees.urls')),
    path('forms/', include('forms_builder.urls')),
    path('reports/', include('reports.urls')),
    path('billing/', include('billing.urls')),
    path('support/', include('support.urls')),
    path('api/', include('accounts.api_urls')),
    path('api/cnpj/<str:cnpj>/', cnpj_lookup, name='cnpj_lookup'),
]

if settings.DEBUG or config('RAILWAY_ENVIRONMENT', default=False) or config('RAILWAY_STATIC_URL', default=False):
    from django.views.static import serve
    urlpatterns += [
        path('media/<path:path>', serve, {'document_root': settings.MEDIA_ROOT}),
    ]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
