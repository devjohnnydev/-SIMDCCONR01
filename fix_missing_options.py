import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'saas_nr01.settings')
django.setup()

from forms_builder.models import FormQuestion

def fix_questions():
    print("Iniciando reparo de opções de questões...")
    
    # Bloco L (135 - 142)
    print("  - Buscando Bloco L (135 - 142)...")
    bloco_l = FormQuestion.objects.filter(order__range=(135, 142), question_type='SINGLE')
    print(f"  - Encontradas {len(bloco_l)} questoes no Bloco L")
    for q in bloco_l:
        if not q.options:
            q.options = ['0', '1', '2', '3']
            q.save()
            print(f"    [OK] Question {q.order} (Bloco L)")

    # Bloco N (151 - 158)
    # 153, 157, 158 são Sim/Não
    print("  - Buscando Bloco N (Sim/Não)...")
    simple_yesno = FormQuestion.objects.filter(order__in=[153, 157, 158], question_type='SINGLE')
    print(f"  - Encontradas {len(simple_yesno)} questoes Sim/Não")
    for q in simple_yesno:
        if not q.options:
            q.options = ['Sim', 'Não']
            q.save()
            print(f"    [OK] Question {q.order} (Sim/Não)")

    # 154 é Regime de Trabalho
    q154 = FormQuestion.objects.filter(order=154, question_type='SINGLE').first()
    if q154 and not q154.options:
        q154.options = ['Presencial', 'Hibrido', 'Home Office']
        q154.save()
        print(f"  - Corrigido: Question 154 (Regime)")

    print("Reparo concluído!")

if __name__ == '__main__':
    fix_questions()
