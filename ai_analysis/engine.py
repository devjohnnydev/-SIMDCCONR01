import os
import json
from groq import Groq
from django.conf import settings
from decouple import config

# Chave API a ser carregada do .env ou do Railway
GROQ_API_KEY = config('GROQ_API_KEY', default='')

client = Groq(api_key=GROQ_API_KEY)

def generate_employee_diagnostic(assignment):
    """
    Usa Groq para analisar respostas e gerar laudo individual (EmployeeDiagnostic).
    Implementa idempotencia: se ja existe, retorna o existente.
    """
    from reports.models import EmployeeDiagnostic
    
    # 1. Verifica se ja existe laudo para este assignment
    existing_diagnostic = getattr(assignment, 'diagnostic', None)
    if existing_diagnostic:
        return existing_diagnostic
        
    # Se nao existe, vamos rodar a IA
    answers = assignment.answers.all().select_related('question')
    
    # Prepara o prompt com as respostas
    context = ""
    for a in answers:
        context += f"Q: {a.question.text}\nA: {a.get_display_value()}\n\n"
        
    prompt = f"""
    Como um agente especialista em SST (Segurança e Saúde no Trabalho) e Psicologia Organizacional, 
    analise as respostas do sistema SIMDCCONR01 para o funcionário {assignment.employee.nome}.
    
    Respostas:
    {context}
    
    Gere um relatório estruturado estritamente em JSON com os seguintes campos:
    1. diagnostico_psicossocial: Resumo da saúde mental e cognitiva.
    2. dissonancia_clima_cultura: Analise se a percepção de clima do funcionário bate com a cultura declarada.
    3. riscos_pgr_gro: Lista de riscos identificados para o PGR/GRO.
    4. recomendacoes_acao: Acões imediatas para a empresa.
    5. encaminhamento_medico: Booleano indicando se precisa de avaliação médica urgente.
    6. justificativa_encaminhamento: Caso verdadeiro, explique o motivo.
    """
    
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "Voce é um especialista em SST e NR-01 que responde exclusivamente em JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={ "type": "json_object" },
            temperature=0.0  # Garante respostas mais deterministicas (idempotencia baseada em mesmas perguntas)
        )
        data = json.loads(response.choices[0].message.content)
        
        # 2. Salva o resultado no banco
        diagnostic = EmployeeDiagnostic.objects.create(
            assignment=assignment,
            diagnostic_data=data
        )
        return diagnostic
        
    except Exception as e:
        import traceback
        print(f"ERROR in AI Analysis: {str(e)}")
        print(traceback.format_exc())
        return {"error": f"Internal Error: {str(e)}", "status": "failed"}

def analyze_survey_results(assignment):
    """
    Funcao legado/auxiliar para retornar apenas o JSON da analise.
    Usado no laudo integrado SIMDCCONR01.
    """
    diagnostic = generate_employee_diagnostic(assignment)
    if isinstance(diagnostic, dict):
        return json.dumps(diagnostic)
    return json.dumps(diagnostic.diagnostic_data)

def generate_consolidated_report(form_instance):
    """
    Gera analise consolidada por departamento ou empresa usando Groq.
    """
    # ... Logica similar para analise agregada
    pass
