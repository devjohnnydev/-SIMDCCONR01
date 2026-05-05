"""
Parte 2: Popula Evolution Snapshots, Risk Score History, Dimension Evolutions,
Predictive AI Alerts, NR Suggestions, Documents e Alerts para ITAU UNIBANCO.
"""
import os, sys, django
os.environ['DJANGO_SETTINGS_MODULE'] = 'saas_nr01.settings'
os.environ['DATABASE_URL'] = 'postgresql://postgres:YPfnUjpIUvylYcYOXWTiwblsUMmBYaSt@metro.proxy.rlwy.net:55676/railway'
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.utils import timezone
from datetime import timedelta, date, datetime
from decimal import Decimal
from companies.models import Company
from accounts.models import User
from evolution.models import EvolutionSnapshot, RiskScoreHistory, DimensionEvolution
from predictive_ai.models import PredictiveAlert, NRSuggestion
from documents.models import Document, DocumentVersion
from alerts.models import Alert

company = Company.objects.filter(nome_fantasia__icontains='ITAU').first()
admin = User.objects.filter(role='ADMIN_MASTER').first()
print(f"Empresa: {company.nome_fantasia} | Admin: {admin.email}")

# === EVOLUTION SNAPSHOTS (6 meses de historico) ===
snapshot_data = [
    {
        'date': date(2025, 11, 15), 'score': Decimal('2.80'), 'classification': 'Atenção',
        'dimensions': {'NR-01|Carga de Trabalho': 2.3, 'NR-01|Autonomia': 3.1, 'NR-01|Relacionamento Interpessoal': 3.5, 'IMCO|Liderança': 2.9, 'IMCO|Comunicação': 2.7, 'FDAC|Fairness': 2.5, 'FDAC|Confiança': 3.0, 'NR-17|Ergonomia Física': 2.4, 'NR-17|Organização do Trabalho': 2.8},
        'sectors': {'Atendimento ao Cliente': 2.2, 'Tecnologia da Informação': 3.1, 'Comercial': 2.6, 'Financeiro': 3.4, 'Recursos Humanos': 3.8, 'Operações': 2.5, 'Compliance e Riscos': 3.7},
        'risks': {'critico': 8, 'atencao': 15, 'adequado': 12, 'forte': 3}, 'respondentes': 25, 'itens': 38, 'pcmso': 3,
    },
    {
        'date': date(2026, 1, 20), 'score': Decimal('3.10'), 'classification': 'Atenção',
        'dimensions': {'NR-01|Carga de Trabalho': 2.5, 'NR-01|Autonomia': 3.3, 'NR-01|Relacionamento Interpessoal': 3.6, 'IMCO|Liderança': 3.1, 'IMCO|Comunicação': 2.9, 'FDAC|Fairness': 2.8, 'FDAC|Confiança': 3.2, 'NR-17|Ergonomia Física': 2.8, 'NR-17|Organização do Trabalho': 3.0},
        'sectors': {'Atendimento ao Cliente': 2.4, 'Tecnologia da Informação': 3.4, 'Comercial': 2.9, 'Financeiro': 3.5, 'Recursos Humanos': 3.9, 'Operações': 2.8, 'Compliance e Riscos': 3.8},
        'risks': {'critico': 5, 'atencao': 14, 'adequado': 16, 'forte': 5}, 'respondentes': 27, 'itens': 40, 'pcmso': 2,
    },
    {
        'date': date(2026, 3, 15), 'score': Decimal('3.45'), 'classification': 'Adequado',
        'dimensions': {'NR-01|Carga de Trabalho': 2.8, 'NR-01|Autonomia': 3.5, 'NR-01|Relacionamento Interpessoal': 3.8, 'IMCO|Liderança': 3.4, 'IMCO|Comunicação': 3.2, 'FDAC|Fairness': 3.1, 'FDAC|Confiança': 3.5, 'NR-17|Ergonomia Física': 3.3, 'NR-17|Organização do Trabalho': 3.4},
        'sectors': {'Atendimento ao Cliente': 2.7, 'Tecnologia da Informação': 3.7, 'Comercial': 3.2, 'Financeiro': 3.6, 'Recursos Humanos': 4.1, 'Operações': 3.2, 'Compliance e Riscos': 4.0},
        'risks': {'critico': 3, 'atencao': 10, 'adequado': 20, 'forte': 9}, 'respondentes': 28, 'itens': 42, 'pcmso': 1,
    },
    {
        'date': date(2026, 5, 1), 'score': Decimal('3.72'), 'classification': 'Adequado',
        'dimensions': {'NR-01|Carga de Trabalho': 3.1, 'NR-01|Autonomia': 3.7, 'NR-01|Relacionamento Interpessoal': 4.0, 'IMCO|Liderança': 3.6, 'IMCO|Comunicação': 3.5, 'FDAC|Fairness': 3.4, 'FDAC|Confiança': 3.8, 'NR-17|Ergonomia Física': 3.6, 'NR-17|Organização do Trabalho': 3.7},
        'sectors': {'Atendimento ao Cliente': 3.0, 'Tecnologia da Informação': 4.0, 'Comercial': 3.5, 'Financeiro': 3.8, 'Recursos Humanos': 4.3, 'Operações': 3.5, 'Compliance e Riscos': 4.2},
        'risks': {'critico': 1, 'atencao': 7, 'adequado': 22, 'forte': 14}, 'respondentes': 28, 'itens': 44, 'pcmso': 0,
    },
]

snap_objs = []
for sd in snapshot_data:
    snap, _ = EvolutionSnapshot.objects.update_or_create(
        company=company, snapshot_date=sd['date'],
        defaults={
            'overall_score': sd['score'], 'overall_classification': sd['classification'],
            'dimension_scores': sd['dimensions'], 'sector_scores': sd['sectors'],
            'risk_count_by_type': sd['risks'], 'total_respondentes': sd['respondentes'],
            'total_itens_analisados': sd['itens'], 'pcmso_alertas': sd['pcmso'],
            'created_by': admin,
        }
    )
    snap_objs.append(snap)
    # Create DimensionEvolution for each snapshot
    for key, media in sd['dimensions'].items():
        inst, dim = key.split('|', 1)
        if media <= 2.4: classif = 'Crítico'
        elif media <= 3.4: classif = 'Atenção'
        elif media <= 4.2: classif = 'Adequado'
        else: classif = 'Forte'
        DimensionEvolution.objects.update_or_create(
            company=company, snapshot=snap, instrumento=inst, dimensao=dim,
            defaults={'media': Decimal(str(media)), 'classificacao': classif, 'total_respostas': sd['respondentes'], 'date': sd['date']}
        )
print(f"Snapshots criados: {len(snap_objs)}")

# === RISK SCORE HISTORY ===
risk_scores = [
    (date(2025, 11, 15), 55, 30, 10, 5, 45, 60),
    (date(2026, 1, 20), 48, 25, 8, 5, 38, 52),
    (date(2026, 3, 15), 39, 20, 5, 3, 30, 42),
    (date(2026, 5, 1), 32, 18, 5, 2, 25, 35),
]
for dt, score, fisico, quimico, biologico, ergonomico, psicossocial in risk_scores:
    RiskScoreHistory.objects.update_or_create(
        company=company, date=dt,
        defaults={'score': score, 'score_fisico': fisico, 'score_quimico': quimico,
                  'score_biologico': biologico, 'score_ergonomico': ergonomico, 'score_psicossocial': psicossocial}
    )
print("Risk Score History criado: 4 registros")

# === PREDICTIVE AI ALERTS ===
ai_alerts = [
    ('SECTOR_DECLINE', 'HIGH', 'Setor "Atendimento ao Cliente" em tendência de queda',
     'O setor de Atendimento ao Cliente apresentou queda consecutiva nos últimos 3 laudos. Score atual: 3.00, Score inicial: 2.20. Apesar da melhora absoluta, a taxa de recuperação está desacelerando comparada aos demais setores.',
     'Recomenda-se intensificar o programa anti-burnout, realizar entrevistas individuais com a equipe e revisar metas de produtividade. Avaliar implementação de pausas obrigatórias conforme NR-17.',
     'Atendimento ao Cliente', '', Decimal('3.00'), Decimal('2.70')),
    ('RISK_GROWING', 'MEDIUM', 'Riscos psicossociais representam 60% do inventário',
     'Análise do inventário de riscos indica que 6 dos 10 perigos cadastrados são de natureza psicossocial. Essa concentração indica necessidade de ações específicas de saúde mental.',
     'Ação recomendada: implementar programa de acompanhamento psicológico conforme NR-1 GRO. Considerar contratação de psicólogo organizacional fixo.',
     '', '', Decimal('6.00'), Decimal('8.00')),
    ('DIMENSION_ALERT', 'HIGH', 'Dimensão "Carga de Trabalho" em nível de ATENÇÃO persistente',
     'A dimensão Carga de Trabalho (NR-01) permanece abaixo de 3.5 em todos os 4 laudos realizados. Embora tenha melhorado de 2.3 para 3.1, continua sendo a dimensão mais crítica.',
     'Ação imediata: revisar distribuição de tarefas nos setores de Atendimento e Comercial. Implementar sistema de rodízio e avaliar necessidade de novas contratações.',
     '', 'Carga de Trabalho', Decimal('3.10'), Decimal('2.80')),
    ('SCORE_PROJECTION', 'MEDIUM', 'Projeção positiva: Score geral pode atingir 4.0 até agosto/2026',
     'Com base na taxa de melhoria dos últimos 4 períodos (média de +0.23 pontos/período), projeta-se que o score geral da empresa pode atingir a classificação "Forte" (4.0+) até agosto de 2026.',
     'Manter as ações em andamento. Focar nos setores com menor evolução (Atendimento e Comercial) para acelerar a recuperação geral.',
     '', '', Decimal('3.72'), Decimal('4.05')),
]
for tt, conf, titulo, desc, rec, setor, dim, atual, proj in ai_alerts:
    PredictiveAlert.objects.update_or_create(
        company=company, titulo=titulo,
        defaults={'trend_type': tt, 'confidence': conf, 'descricao': desc, 'recomendacao': rec,
                  'setor': setor, 'dimensao': dim, 'score_atual': atual, 'score_projetado': proj,
                  'data_points': []}
    )
print(f"Alertas preditivos criados: {len(ai_alerts)}")

# === NR SUGGESTIONS (seed) ===
from predictive_ai.services import seed_nr_suggestions
nr_count = seed_nr_suggestions()
print(f"Sugestões NR criadas: {nr_count}")

# === DOCUMENTS ===
docs_data = [
    ('PGR', 'PGR — Programa de Gerenciamento de Riscos 2025/2026', 'Programa de Gerenciamento de Riscos conforme NR-1, contemplando inventário de riscos, planos de ação e medidas de controle para todos os setores do ITAU UNIBANCO.', 'ACTIVE', date(2025, 11, 20), date(2026, 11, 20), ['NR-1 (2024.1)', 'NR-7 (2024.1)']),
    ('PCMSO', 'PCMSO — Programa de Controle Médico 2025/2026', 'Programa de Controle Médico de Saúde Ocupacional com monitoramento de indicadores de saúde mental e física dos colaboradores.', 'ACTIVE', date(2025, 12, 1), date(2026, 12, 1), ['NR-7 (2024.1)']),
    ('AEP', 'AEP — Avaliação Ergonômica Preliminar - Setor TI', 'Avaliação ergonômica preliminar do setor de Tecnologia da Informação, identificando inadequações no mobiliário e recomendações de ajuste.', 'ACTIVE', date(2026, 1, 15), date(2027, 1, 15), ['NR-17 (2024.1)']),
    ('LAUDO', 'Laudo Diagnóstico Psicossocial — 1º Ciclo', 'Primeiro laudo diagnóstico psicossocial aplicado via plataforma SIMDCCONR01, contemplando análise de clima, riscos e recomendações.', 'SUPERSEDED', date(2025, 11, 15), date(2026, 5, 15), ['NR-1 (2024.1)']),
    ('LAUDO', 'Laudo Diagnóstico Psicossocial — 2º Ciclo', 'Segundo ciclo de avaliação psicossocial com comparativo evolutivo em relação ao primeiro laudo.', 'SUPERSEDED', date(2026, 1, 20), date(2026, 7, 20), ['NR-1 (2024.1)']),
    ('LAUDO', 'Laudo Diagnóstico Psicossocial — 3º Ciclo', 'Terceiro ciclo de avaliação mostrando evolução positiva em todas as dimensões avaliadas.', 'ACTIVE', date(2026, 3, 15), date(2026, 9, 15), ['NR-1 (2024.1)']),
    ('LTCAT', 'LTCAT — Laudo Técnico de Condições Ambientais', 'Laudo técnico de condições ambientais do trabalho para fins previdenciários.', 'ACTIVE', date(2026, 2, 1), date(2027, 2, 1), ['NR-1 (2024.1)', 'NR-15']),
]
for tipo, titulo, desc, status, emissao, validade, normas in docs_data:
    doc, _ = Document.objects.update_or_create(
        company=company, titulo=titulo,
        defaults={'tipo': tipo, 'descricao': desc, 'status': status,
                  'data_emissao': emissao, 'validade': validade,
                  'normas_aplicadas': normas, 'created_by': admin}
    )
    DocumentVersion.objects.get_or_create(
        document=doc, versao=1,
        defaults={'alterado_por': admin, 'motivo_alteracao': 'Versão inicial'}
    )
print(f"Documentos criados: {len(docs_data)}")

# === ALERTS ===
now = timezone.now()
alerts_data = [
    ('RISK_CRITICAL', 'CRITICAL', 'Risco INTOLERÁVEL sem plano de ação adequado', 'O perigo "Exposição a estresse crônico por metas abusivas" no setor de Atendimento ao Cliente foi avaliado como Intolerável (P5×S4=20) e o plano de ação está com apenas 60% de conclusão.', False),
    ('DEADLINE_APPROACHING', 'WARNING', 'Prazo vencendo em 5 dias', 'A ação "Programa Anti-Burnout Atendimento" vence em 30/07/2026. Responsável: Ana Paula Ferreira.', False),
    ('REPORT_EXPIRING', 'WARNING', 'Documento expirando em 15 dias', 'O documento "Laudo Diagnóstico Psicossocial — 3º Ciclo" expira em 15/09/2026. Providencie a atualização.', False),
    ('SCORE_DECLINE', 'INFO', 'Score de risco melhorou significativamente', 'O score de risco da empresa caiu de 55 para 32 pontos nos últimos 6 meses. Faixa atual: Médio Risco. A tendência é positiva e indica eficácia das ações implementadas.', True),
    ('HEALTH_DROP', 'WARNING', 'Queda no índice de saúde do setor Comercial', 'O setor Comercial apresentou queda de 0.3 pontos no índice de saúde mental entre o 2º e 3º ciclo de avaliação. Monitorar de perto.', False),
    ('PCMSO_ALERT', 'CRITICAL', 'Alerta PCMSO: 3 colaboradores com indicadores críticos', 'O PCMSO identificou 3 colaboradores no setor de Atendimento com indicadores de estresse acima do limiar. Encaminhamento para avaliação médica recomendado.', False),
    ('DEADLINE_OVERDUE', 'CRITICAL', 'Plano de ação vencido há 10 dias', 'A ação "Programa Saúde Mental Corporativa" deveria ter sido iniciada em 01/02/2026 mas permanece PENDENTE. Responsável: Ana Paula Ferreira.', False),
    ('FORM_LOW_RESPONSE', 'WARNING', 'Baixa adesão ao formulário no setor Operações', 'O setor de Operações atingiu apenas 75% de taxa de resposta no último formulário. Meta é 95%. Reforçar comunicação.', True),
    ('RISK_HIGH', 'WARNING', 'Novo risco ergonômico identificado no setor TI', 'Foi registrado um novo risco ergonômico (Moderado) relacionado ao uso prolongado de computador sem pausas adequadas. Necessário avaliar medidas de controle.', False),
    ('PAYMENT_DUE', 'INFO', 'Fatura mensal processada com sucesso', 'A fatura referente ao mês de abril/2026 foi processada automaticamente no valor do plano contratado.', True),
]
for tipo, sev, titulo, msg, is_read in alerts_data:
    Alert.objects.update_or_create(
        company=company, titulo=titulo,
        defaults={'tipo': tipo, 'severidade': sev, 'mensagem': msg,
                  'is_read': is_read, 'read_at': now if is_read else None}
    )
print(f"Alertas criados: {len(alerts_data)}")

print("=== PARTE 2 CONCLUIDA ===")
