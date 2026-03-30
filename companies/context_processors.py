"""
Context processor para injetar dados da empresa em todos os templates.
"""


def company_context(request):
    """
    Adiciona dados da empresa ao contexto de todos os templates.
    Permite personalizacao visual (logo, cores) dinamica.
    """
    context = {
        'current_company': None,
        'company_logo': None,
        'company_primary_color': '#0d6efd',
        'company_secondary_color': '#6c757d',
    }
    
    if hasattr(request, 'current_company') and request.current_company:
        company = request.current_company
        context['current_company'] = company
        context['company_logo'] = company.logo.url if company.logo else None
        context['company_primary_color'] = company.cor_primaria
        context['company_secondary_color'] = company.cor_secundaria
    
    return context
