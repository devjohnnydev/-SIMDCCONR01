"""
Middleware para carregar dados da empresa do usuario logado.
Injeta informacoes da empresa em todas as requisicoes.
"""


class CompanyMiddleware:
    """
    Middleware que adiciona a empresa do usuario logado ao request.
    Permite acesso facil aos dados da empresa em views e templates.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        request.current_company = None
        
        if request.user.is_authenticated:
            if hasattr(request.user, 'company') and request.user.company:
                request.current_company = request.user.company
        
        response = self.get_response(request)
        return response
