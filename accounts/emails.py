from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings

def send_company_welcome_contract(company):
    """
    Envia e-mail de boas-vindas e formalização para a nova empresa.
    """
    subject = f'Formalização de Contrato SIMDCCONR01 - {company.nome_fantasia}'
    
    protocolo = f"SIMDC-{company.id}-{company.cnpj[:4]}"
    context = {
        'company': company,
        'protocolo': protocolo,
        'verify_url': f"https://safeclima.com.br/accounts/verify/contract/{protocolo}/",
        'support_email': 'suporte@simdcconr01.com.br'
    }
    
    html_content = render_to_string('emails/company_welcome_contract.html', context)
    text_content = strip_tags(html_content)
    
    try:
        send_mail(
            subject,
            text_content,
            settings.DEFAULT_FROM_EMAIL,
            [company.responsavel_email],
            html_message=html_content,
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Erro ao enviar e-mail: {str(e)}")
        return False
