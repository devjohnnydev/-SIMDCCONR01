from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags

def send_form_publication_notification(assignment):
    """
    Envia e-mail para o funcionário informando sobre o novo formulário
    e seus dados de acesso (E-mail e CPF).
    """
    employee = assignment.employee
    form = assignment.form_instance
    
    subject = f'Nova Pesquisa Disponível: {form.title}'
    
    context = {
        'employee': employee,
        'form': form,
        'login_email': employee.email,
        'password_hint': employee.cpf,
        'login_url': settings.LOGIN_URL if hasattr(settings, 'LOGIN_URL') else '/accounts/login/',
    }
    
    html_message = render_to_string('forms_builder/emails/publication_email.html', context)
    plain_message = strip_tags(html_message)
    
    try:
        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [employee.email],
            html_message=html_message,
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Erro ao enviar e-mail de publicação para {employee.email}: {str(e)}")
        return False

def send_form_activity_notification(assignment, activity_type='ENTRY'):
    """
    Notifica a empresa quando um funcionário entra ou finaliza a pesquisa.
    activity_type: 'ENTRY' ou 'SUBMISSION'
    """
    employee = assignment.employee
    form = assignment.form_instance
    company = form.company
    
    if not company.responsavel_email:
        return False
        
    if activity_type == 'ENTRY':
        subject = f'Atividade: Funcionário acessou a pesquisa - {form.title}'
        status_text = "entrou na pesquisa (ainda não respondeu)"
    else:
        subject = f'Atividade: Pesquisa respondida - {form.title}'
        status_text = "finalizou e enviou a resposta da pesquisa"
        
    context = {
        'employee': employee,
        'form': form,
        'company': company,
        'status_text': status_text,
        'activity_type': activity_type,
    }
    
    html_message = render_to_string('forms_builder/emails/activity_notification.html', context)
    plain_message = strip_tags(html_message)
    
    try:
        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [company.responsavel_email],
            html_message=html_message,
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Erro ao enviar e-mail de atividade para a empresa {company.nome_fantasia}: {str(e)}")
        return False
