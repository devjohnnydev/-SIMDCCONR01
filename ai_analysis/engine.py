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

def generate_department_diagnostic(company, sector_name, form_instance, user=None):
    """
    Gera analise consolidada por departamento usando Groq.
    Categoriza clima, riscos e sugestoes para a gestao da empresa.
    """
    from reports.models import DepartmentDiagnostic
    from forms_builder.models import FormAssignment, FormAnswer
    
    # 1. Busca assignments concluidos do setor
    assignments = FormAssignment.objects.filter(
        form_instance=form_instance,
        employee__company=company,
        employee__setor=sector_name,
        status='COMPLETED'
    )
    
    if not assignments.exists():
        return {"error": "Nenhuma resposta concluída encontrada para este departamento.", "status": "failed"}

    # 2. Agrega respostas para o prompt
    all_answers = FormAnswer.objects.filter(assignment__in=assignments).select_related('question')
    
    aggregation = {}
    for a in all_answers:
        q_text = a.question.text
        if q_text not in aggregation:
            aggregation[q_text] = []
        # Limitamos a amostra para nao estourar o contexto se houver muitos funcionarios
        if len(aggregation[q_text]) < 20: 
            aggregation[q_text].append(a.get_display_value())

    context = ""
    for q_text, values in aggregation.items():
        context += f"Pergunta: {q_text}\nRespostas (amostra): {', '.join(map(str, values))}\n\n"

    prompt = f"""
    Como um consultor sênior em Psicologia Organizacional e SST, analise o CLIMA SOCIOEMOCIONAL do departamento '{sector_name}' da empresa {company.nome_fantasia}.
    Baseie-se nestes dados agregados (anônimos) de {assignments.count()} funcionários:
    
    {context}
    
    Gere um relatório JSON rigoroso com:
    1. clima_geral: Resumo do estado emocional coletivo.
    2. pontos_fortes: O que está funcionando bem no setor.
    3. areas_alerta: Riscos de clima ou esgotamento identificados.
    4. sugestoes_gestao: Acões recomendadas para o gestor do setor.
    5. indice_bem_estar: Valor de 0 a 100.
    """

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "Você é um analista de clima organizacional que responde exclusivamente em JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={ "type": "json_object" },
            temperature=0.2
        )
        data = json.loads(response.choices[0].message.content)
        
        # 3. Salva ou atualiza o laudo do departamento
        diagnostic, created = DepartmentDiagnostic.objects.update_or_create(
            company=company,
            setor=sector_name,
            form_instance=form_instance,
            defaults={
                'diagnostic_data': data,
                'generated_by': user
            }
        )
        return diagnostic
        
    except Exception as e:
        print(f"ERROR in Department AI Analysis: {str(e)}")
        return {"error": f"Erro na IA: {str(e)}", "status": "failed"}

