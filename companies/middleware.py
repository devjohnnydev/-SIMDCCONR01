"""
Middleware para carregar dados da empresa do usuario logado.
Injeta informacoes da empresa em todas as requisicoes.
Bloqueia COMPANY_ADMIN sem plano ativo — redireciona para pricing.
Verifica expiração de plano por tempo e desativa automaticamente.
"""
from django.shortcuts import redirect
from django.contrib import messages
from django.utils import timezone


# URLs que empresas sem plano podem acessar
PLAN_EXEMPT_PREFIXES = (
    '/billing/',
    '/accounts/logout/',
    '/accounts/login/',
    '/accounts/signup/',
    '/accounts/pending-approval/',
    '/static/',
    '/media/',
    '/admin/',
    '/support/',
)


class CompanyMiddleware:
    """
    Middleware que adiciona a empresa do usuario logado ao request.
    Permite personalizacao visual (logo, cores) dinamica.
    Redireciona COMPANY_ADMIN sem plano para a pagina de pricing.
    Detecta expiração de plano e desativa automaticamente.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.current_company = None

        if request.user.is_authenticated:
            if hasattr(request.user, 'company') and request.user.company:
                company = request.user.company
                request.current_company = company

                # ── Verificar expiração do plano por tempo ──
                if (
                    company.plan
                    and company.current_period_end
                    and company.subscription_status in ('active', 'trialing')
                    and company.current_period_end <= timezone.now()
                ):
                    # Plano expirou — desativar automaticamente
                    company.subscription_status = 'expired'
                    company.save(update_fields=['subscription_status'])

                    # Marcar assinaturas ativas como expiradas
                    from billing.models import Subscription
                    Subscription.objects.filter(
                        company=company, status='ACTIVE'
                    ).update(status='EXPIRED')

                    if request.user.role == 'COMPANY_ADMIN':
                        messages.warning(
                            request,
                            'Seu plano expirou. Renove sua assinatura para continuar '
                            'utilizando todas as funcionalidades do sistema.'
                        )

                # ── Bloqueia COMPANY_ADMIN sem plano ativo ──
                if (
                    request.user.role == 'COMPANY_ADMIN'
                    and not company.has_active_plan
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
