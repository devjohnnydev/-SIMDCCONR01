import os
import json
from groq import Groq
from django.conf import settings
from decouple import config

# Chave API a ser carregada do .env ou do Railway
GROQ_API_KEY = config('GROQ_API_KEY', default='')

client = Groq(api_key=GROQ_API_KEY)

def analyze_survey_results(assignment):
    """
    Usa Groq (Llama-3.3-70b) para analisar as 160 respostas do questionario SIMDCCONR01.
    Gera diagnostico, recomendacoes PGR/GRO e encaminhamento medico se necessário.
    """
    answers = assignment.answers.all().select_related('question')
    
    # Prepara o prompt com as respostas
    context = ""
    for a in answers:
        context += f"Q: {a.question.text}\nA: {a.get_display_value()}\n\n"
    
    prompt = f"""
    Como um agente especialista em SST (Segurança e Saúde no Trabalho) e Psicologia Organizacional, 
    analise as seguintes 160 respostas do sistema SIMDCCONR01 para o funcionário {assignment.employee.nome}.
    
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
            response_format={ "type": "json_object" }
        )
        return response.choices[0].message.content
    except Exception as e:
        return json.dumps({"error": str(e), "status": "failed"})

def generate_consolidated_report(form_instance):
    """
    Gera analise consolidada por departamento ou empresa usando Groq.
    """
    # ... Logica similar para analise agregada
    pass
