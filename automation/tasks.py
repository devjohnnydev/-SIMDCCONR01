from datetime import timedelta
from django.utils import timezone
from forms_builder.models import FormAssignment, FormInstance

def check_reapplications():
    """
    Verifica funcionarios que concluiram o questionario SIMDCCONR01
    ha mais de 6 meses (180 dias) e cria novas atribuicoes.
    """
    threshold = timezone.now() - timedelta(days=180)
    
    # Busca atribuicoes concluidas ha 180 dias ou mais
    completed_assignments = FormAssignment.objects.filter(
        status='COMPLETED',
        completed_at__lte=threshold,
        form_instance__template__category='SIMDCCONR01'
    )
    
    for assignment in completed_assignments:
        company = assignment.employee.company
        template = assignment.form_instance.template
        
        # Busca ou cria a instancia atual de coleta da empresa
        current_instance = FormInstance.objects.filter(
            company=company,
            template=template,
            status='ACTIVE',
            end_date__gte=timezone.now()
        ).first()
        
        if current_instance:
            # Verifica se ja existe uma atribuicao pendente ou ativa para este periodo
            exists = FormAssignment.objects.filter(
                form_instance=current_instance,
                employee=assignment.employee
            ).exists()
            
            if not exists:
                FormAssignment.objects.create(
                    form_instance=current_instance,
                    employee=assignment.employee,
                    status='PENDING'
                )
                print(f"Reaplicacao semestral criada para: {assignment.employee.nome} ({company.nome_fantasia})")

def send_notifications():
    """
    Simula envio de notificacoes via WhatsApp/SMS/Email.
    """
    pending = FormAssignment.objects.filter(status='PENDING')
    for p in pending:
        msg = (
            f"Notificacao enviada para {p.employee.nome}: "
            f"Seu questionario SIMDCCONR01 ja esta disponivel para reaplicacao semestral."
        )
        print(msg)
