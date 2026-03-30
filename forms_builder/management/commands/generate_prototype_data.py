import random
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from companies.models import Company
from employees.models import Employee
from forms_builder.models import FormTemplate, FormInstance, FormAssignment, FormAnswer, FormQuestion

User = get_user_model()

class Command(BaseCommand):
    help = 'Gera dados de prototipo: 10 respondentes com 160 respostas cada'

    def handle(self, *args, **options):
        # 1. Busca ou cria empresa de teste
        company, _ = Company.objects.get_or_create(
            cnpj='12345678000199',
            defaults={
                'razao_social': 'Empresa de Teste SIMDCCONR01 LTDA',
                'nome_fantasia': 'Teste ISMCBE',
                'segmento': 'INDUSTRIA',
            }
        )

        # 2. Busca o template SIMDCCONR01
        template = FormTemplate.objects.get(category='SIMDCCONR01')
        questions = template.questions.all()

        # 3. Cria instancia de coleta
        instance, _ = FormInstance.objects.get_or_create(
            company=company,
            template=template,
            status='ACTIVE',
            defaults={
                'title': 'Coleta Protótipo SIMDCCONR01',
                'start_date': timezone.now() - timedelta(days=1),
                'end_date': timezone.now() + timedelta(days=30),
                'is_anonymous': False
            }
        )

        # 4. Cria 10 funcionários e suas respostas
        for i in range(1, 11):
            cpf = f'{i:011d}'
            email = f'funcionario{i}@teste.com.br'
            employee, _ = Employee.objects.get_or_create(
                company=company,
                cpf=cpf,
                defaults={
                    'nome': f'Funcionário Exemplo {i}',
                    'email': email,
                    'setor': random.choice(['RH', 'Produção', 'TI', 'Vendas']),
                    'cargo': 'Analista',
                    'data_admissao': timezone.now().date() - timedelta(days=365)
                }
            )

            # Atribuição
            assignment, _ = FormAssignment.objects.get_or_create(
                form_instance=instance,
                employee=employee,
                defaults={'status': 'COMPLETED', 'completed_at': timezone.now()}
            )
            assignment.status = 'COMPLETED' # Garantir que está concluído
            assignment.completed_at = timezone.now()
            assignment.save()

            # Respostas (160 itens)
            for q in questions:
                # Se já existir resposta, pula
                if FormAnswer.objects.filter(assignment=assignment, question=q).exists():
                    continue
                    
                answer = FormAnswer(assignment=assignment, question=q)
                
                if q.question_type == 'SCALE':
                    answer.numeric_value = random.randint(1, 5)
                elif q.question_type == 'SCALE_10':
                    answer.numeric_value = random.randint(1, 10)
                elif q.question_type == 'YESNO':
                    answer.boolean_value = random.choice([True, False])
                elif q.question_type == 'SINGLE':
                    answer.selected_options = [random.choice(['Opcao A', 'Opcao B', 'Opcao C'])]
                elif q.question_type == 'NUMBER':
                    answer.numeric_value = random.randint(0, 40)
                elif q.question_type == 'TEXT':
                    answer.text_value = "Minha percepção sobre os últimos 3 meses é de foco e comprometimento."
                
                answer.save()

            self.stdout.write(f'  - Respostas geradas para {employee.nome}')

        self.stdout.write(self.style.SUCCESS('Dados de protótipo (10 respondentes) gerados com sucesso!'))
