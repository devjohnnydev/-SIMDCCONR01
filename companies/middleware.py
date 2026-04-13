"""
Middleware para carregar dados da empresa do usuario logado.
Injeta informacoes da empresa em todas as requisicoes.
Bloqueia COMPANY_ADMIN sem plano ativo — redireciona para pricing.
"""
from django.shortcuts import redirect
from django.contrib import messages


# URLs que empresas sem plano podem acessar
PLAN_EXEMPT_PREFIXES = (
    '/billing/',
    '/accounts/logout/',
    '/accounts/login/',
    '/static/',
    '/media/',
    '/admin/',
)


class CompanyMiddleware:
    """
    Middleware que adiciona a empresa do usuario logado ao request.
    Permite personalizacao visual (logo, cores) dinamica.
    Redireciona COMPANY_ADMIN sem plano para a pagina de pricing.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.current_company = None

        if request.user.is_authenticated:
            if hasattr(request.user, 'company') and request.user.company:
                request.current_company = request.user.company

                # Bloqueia COMPANY_ADMIN sem plano ativo
                if (
                    request.user.role == 'COMPANY_ADMIN'
                    and not request.user.company.has_active_plan
                    and not any(request.path.startswith(p) for p in PLAN_EXEMPT_PREFIXES)
                ):
                    messages.warning(
                        request,
                        'Sua empresa ainda não possui um plano ativo. '
                        'Escolha um plano para desbloquear todas as funcionalidades.'
                    )
                    return redirect('billing:pricing')

        response = self.get_response(request)
        return response
