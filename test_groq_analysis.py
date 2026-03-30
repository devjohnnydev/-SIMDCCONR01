import os
import json
import sys

# Mocking Django environment for standalone test
class MockQuestion:
    def __init__(self, text):
        self.text = text

class MockAnswer:
    def __init__(self, question, value):
        self.question = question
        self.value = value
    def get_display_value(self):
        return str(self.value)

class MockAssignment:
    def __init__(self, employee_name):
        self.employee = type('obj', (object,), {'nome': employee_name})
        self.answers = self
    def all(self):
        return self
    def select_related(self, *args):
        return [
            MockAnswer(MockQuestion("Como você se sente em relação ao seu volume de trabalho?"), "Muito sobrecarregado"),
            MockAnswer(MockQuestion("Existe clareza sobre os objetivos da empresa?"), "Não, sinto que as direções mudam constantemente"),
            MockAnswer(MockQuestion("Você se sente seguro operando as máquinas atuais?"), "Sim, mas a manutenção poderia ser mais frequente"),
            MockAnswer(MockQuestion("Como avalia a liderança direta?"), "Autoritária e pouco aberta ao diálogo")
        ]

# Import the analysis function
# Fix path to allow importing from ai_analysis
sys.path.append(os.getcwd())
try:
    from ai_analysis.engine import analyze_survey_results
    
    print("--- INICIANDO TESTE DE ANÁLISE GROQ (Llama-3.3-70b) ---")
    mock_assignment = MockAssignment("João da Silva")
    
    result_json = analyze_survey_results(mock_assignment)
    result = json.loads(result_json)
    
    print("\n[RESULTADO DA IA]")
    print(json.dumps(result, indent=4, ensure_ascii=False))
    print("\n--- TESTE CONCLUÍDO COM SUCESSO ---")
except Exception as e:
    print(f"\n[ERRO NO TESTE]: {e}")
    print("Certifique-se de que a biblioteca 'groq' está instalada: pip install groq")
