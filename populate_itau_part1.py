"""
Parte 1: Popula Funcionarios, Riscos, Avaliacoes, Medidas de Controle e Planos de Acao
para a empresa ITAU UNIBANCO.
"""
import os, sys, django
os.environ['DJANGO_SETTINGS_MODULE'] = 'saas_nr01.settings'
os.environ['DATABASE_URL'] = 'postgresql://postgres:YPfnUjpIUvylYcYOXWTiwblsUMmBYaSt@metro.proxy.rlwy.net:55676/railway'
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.utils import timezone
from datetime import timedelta, date
from decimal import Decimal
from companies.models import Company
from employees.models import Employee
from accounts.models import User
from risk_management.models import HazardRegistry, RiskAssessment, ControlMeasure, ActionPlan

# Find ITAU
company = Company.objects.filter(nome_fantasia__icontains='ITAU').first()
if not company:
    print("ERRO: Empresa ITAU nao encontrada!")
    sys.exit(1)
print(f"Empresa encontrada: {company.nome_fantasia} (ID={company.pk})")

# Get or create admin user
admin = User.objects.filter(role='ADMIN_MASTER').first()
if not admin:
    print("ERRO: Admin master nao encontrado!")
    sys.exit(1)
print(f"Admin: {admin.email}")

# === FUNCIONARIOS ===
setores_cargos = {
    'Tecnologia da Informação': [
        ('Carlos Eduardo Silva', 'Desenvolvedor Senior', '12345678901'),
        ('Mariana Oliveira Costa', 'Analista de Sistemas', '12345678902'),
        ('Rafael Mendes Santos', 'Coordenador de TI', '12345678903'),
        ('Juliana Pereira Lima', 'Analista de Dados', '12345678904'),
        ('Fernando Alves Rocha', 'DevOps Engineer', '12345678905'),
    ],
    'Recursos Humanos': [
        ('Ana Paula Ferreira', 'Gerente de RH', '22345678901'),
        ('Beatriz Souza Martins', 'Analista de RH', '22345678902'),
        ('Luciana Barbosa Reis', 'Coordenadora de T&D', '22345678903'),
    ],
    'Atendimento ao Cliente': [
        ('Pedro Henrique Gomes', 'Supervisor de Atendimento', '32345678901'),
        ('Camila Rodrigues Nunes', 'Atendente Senior', '32345678902'),
        ('Thiago Nascimento Dias', 'Atendente Pleno', '32345678903'),
        ('Amanda Lopes Vieira', 'Atendente Junior', '32345678904'),
        ('Bruno Castro Filho', 'Atendente Junior', '32345678905'),
        ('Larissa Melo Cardoso', 'Atendente Pleno', '32345678906'),
        ('Diego Araujo Pinto', 'Atendente Senior', '32345678907'),
    ],
    'Comercial': [
        ('Roberto Lima Carvalho', 'Gerente Comercial', '42345678901'),
        ('Patricia Moura Teixeira', 'Executiva de Contas', '42345678902'),
        ('Gustavo Freitas Ribeiro', 'Executivo de Contas', '42345678903'),
        ('Vanessa Correia Andrade', 'Analista Comercial', '42345678904'),
    ],
    'Financeiro': [
        ('Marcos Antonio Duarte', 'Controller', '52345678901'),
        ('Claudia Rezende Amaral', 'Analista Financeiro', '52345678902'),
        ('Renato Borges Pereira', 'Analista Contabil', '52345678903'),
    ],
    'Compliance e Riscos': [
        ('Adriana Campos Silveira', 'Diretora de Compliance', '62345678901'),
        ('Eduardo Monteiro Braga', 'Analista de Riscos', '62345678902'),
    ],
    'Operações': [
        ('Sandra Maria Tavares', 'Supervisora de Operações', '72345678901'),
        ('Leandro Fonseca Machado', 'Operador Senior', '72345678902'),
        ('Tatiane Nogueira Cruz', 'Operadora Pleno', '72345678903'),
        ('Alexandre Costa Ramos', 'Operador Junior', '72345678904'),
    ],
}

emp_count = 0
for setor, pessoas in setores_cargos.items():
    for nome, cargo, cpf in pessoas:
        email = nome.lower().replace(' ', '.').replace('á','a').replace('é','e').replace('í','i').replace('ó','o').replace('ú','u').replace('ã','a').replace('ç','c') + '@itau.internal'
        emp, created = Employee.objects.update_or_create(
            company=company, cpf=cpf,
            defaults={
                'nome': nome, 'email': email, 'setor': setor, 'cargo': cargo,
                'turno': 'FULL', 'data_admissao': date(2024, 1, 15) + timedelta(days=hash(nome) % 365),
                'status': 'ACTIVE',
            }
        )
        if created: emp_count += 1
print(f"Funcionarios criados/atualizados: {emp_count}")

# === RISCOS (HazardRegistry) ===
hazards_data = [
    ('Atendimento ao Cliente', 'Atendente', 'Atendimento telefonico continuo', 'Exposicao a estresse cronico por metas abusivas e clientes agressivos', 'Pressao por produtividade', 'PSICOSSOCIAL', 'NR-1'),
    ('Atendimento ao Cliente', 'Atendente', 'Uso prolongado de headset', 'Exposicao a ruido continuo acima de 85dB pelo headset', 'Headset mal calibrado', 'FISICO', 'NR-1'),
    ('Tecnologia da Informação', 'Desenvolvedor', 'Trabalho em tela por mais de 6h', 'Risco ergonomico por postura inadequada e uso prolongado de computador', 'Estacao de trabalho', 'ERGONOMICO', 'NR-17'),
    ('Tecnologia da Informação', 'Analista', 'Plantoes noturnos', 'Disturbio do ciclo circadiano por plantoes frequentes', 'Escala de plantao', 'PSICOSSOCIAL', 'NR-1'),
    ('Comercial', 'Executivo de Contas', 'Deslocamento externo', 'Risco de acidente de transito em visitas a clientes', 'Veiculo corporativo', 'ACIDENTE', 'NR-1'),
    ('Comercial', 'Gerente Comercial', 'Gestao de equipe com metas agressivas', 'Sindrome de Burnout por sobrecarga decisoria e pressao por resultados', 'Meta trimestral', 'PSICOSSOCIAL', 'NR-1'),
    ('Operações', 'Operador', 'Manuseio de equipamentos de TI', 'Risco eletrico ao manipular servidores e cabeamento', 'Sala de servidores', 'ACIDENTE', 'NR-12'),
    ('Operações', 'Operador', 'Trabalho em ambiente climatizado abaixo de 18C', 'Exposicao a temperatura baixa no datacenter', 'Datacenter', 'FISICO', 'NR-1'),
    ('Financeiro', 'Analista', 'Fechamento contabil sob pressao', 'Ansiedade e estresse por prazos apertados de fechamento', 'Calendario fiscal', 'PSICOSSOCIAL', 'NR-1'),
    ('Recursos Humanos', 'Analista de RH', 'Atendimento a demissoes e conflitos', 'Sobrecarga emocional por lidar com situacoes de crise', 'Rotina de gestao de pessoas', 'PSICOSSOCIAL', 'NR-1'),
]

statuses = ['ACTIVE','ACTIVE','ACTIVE','MITIGATED','ACTIVE','ACTIVE','ELIMINATED','ACTIVE','ACTIVE','MITIGATED']
h_dates = [date(2025,8,10), date(2025,9,5), date(2025,10,1), date(2025,11,15), date(2025,12,1), date(2026,1,10), date(2026,1,20), date(2026,2,5), date(2026,3,1), date(2026,3,15)]

hazard_objs = []
for i, (setor, funcao, atividade, desc, fonte, tipo, norma) in enumerate(hazards_data):
    h, _ = HazardRegistry.objects.update_or_create(
        company=company, descricao_perigo=desc,
        defaults={
            'setor': setor, 'funcao': funcao, 'atividade': atividade,
            'fonte_geradora': fonte, 'tipo_risco': tipo, 'norma_referencia': norma,
            'status': statuses[i], 'identified_by': admin, 'identified_at': timezone.make_aware(timezone.datetime.combine(h_dates[i], timezone.datetime.min.time())),
        }
    )
    hazard_objs.append(h)
print(f"Perigos registrados: {len(hazard_objs)}")

# === AVALIACOES DE RISCO ===
assess_data = [(5,4),(3,3),(4,3),(3,2),(4,5),(5,3),(2,5),(3,2),(4,3),(3,2)]
assess_objs = []
for i, h in enumerate(hazard_objs):
    p, s = assess_data[i]
    a, _ = RiskAssessment.objects.update_or_create(
        hazard=h, avaliado_por=admin,
        defaults={'probabilidade': p, 'severidade': s, 'justificativa': f'Avaliacao tecnica do risco no setor {h.setor}', 'data_avaliacao': h_dates[i] + timedelta(days=5)}
    )
    assess_objs.append(a)
print(f"Avaliacoes criadas: {len(assess_objs)}")

# === MEDIDAS DE CONTROLE ===
controls = [
    (0, 'ADMINISTRATIVA', 'Implementar rodizio de atendentes a cada 2 horas', 'Ana Paula Ferreira'),
    (0, 'EPI', 'Fornecer headsets com cancelamento de ruido', 'Rafael Mendes Santos'),
    (1, 'EPC', 'Calibrar volume maximo dos headsets para 80dB', 'Rafael Mendes Santos'),
    (2, 'ENGENHARIA', 'Substituir mobiliario por mesas com regulagem de altura', 'Sandra Maria Tavares'),
    (2, 'ADMINISTRATIVA', 'Implementar ginastica laboral 2x ao dia', 'Ana Paula Ferreira'),
    (4, 'ADMINISTRATIVA', 'Treinamento de direcao defensiva obrigatorio', 'Roberto Lima Carvalho'),
    (5, 'ORGANIZACIONAL', 'Programa de acompanhamento psicologico mensal', 'Ana Paula Ferreira'),
    (6, 'ELIMINACAO', 'Substituir cabeamento exposto por infraestrutura selada', 'Sandra Maria Tavares'),
    (7, 'EPI', 'Fornecer jaquetas termicas para equipe do datacenter', 'Sandra Maria Tavares'),
    (8, 'ADMINISTRATIVA', 'Redistribuir tarefas de fechamento entre equipe', 'Marcos Antonio Duarte'),
]

for idx, tipo, desc, resp in controls:
    impl = idx in [1, 6, 7]
    ControlMeasure.objects.update_or_create(
        risk_assessment=assess_objs[idx], descricao=desc,
        defaults={'tipo': tipo, 'responsavel': resp, 'prazo': date(2026,6,30),
                  'implementada': impl, 'data_implementacao': date(2026,3,1) if impl else None,
                  'eficacia_verificada': idx == 7, 'data_verificacao': date(2026,4,1) if idx == 7 else None}
    )
print(f"Medidas de controle criadas: {len(controls)}")

# === PLANOS DE ACAO ===
plans = [
    ('Programa Anti-Burnout Atendimento', 'Implementar programa completo de prevencao ao burnout no setor de Atendimento', 'Ana Paula Ferreira', 'URGENTE', 'EM_ANDAMENTO', 60),
    ('Adequacao Ergonomica TI', 'Trocar todo mobiliario do setor de TI por mesas ajustaveis e cadeiras ergonomicas', 'Sandra Maria Tavares', 'ALTA', 'EM_ANDAMENTO', 40),
    ('Treinamento Direcao Defensiva', 'Contratar empresa especializada para treinamento de direcao defensiva', 'Roberto Lima Carvalho', 'MEDIA', 'CONCLUIDO', 100),
    ('Reforma Datacenter - Seguranca Eletrica', 'Substituir toda infraestrutura eletrica exposta do datacenter', 'Sandra Maria Tavares', 'URGENTE', 'CONCLUIDO', 100),
    ('Programa Saude Mental Corporativa', 'Contratar psicologo organizacional fixo e implementar canal de acolhimento', 'Ana Paula Ferreira', 'ALTA', 'PENDENTE', 0),
    ('Revisao de Metas Comerciais', 'Reavaliar metas trimestrais do setor comercial para niveis sustentaveis', 'Roberto Lima Carvalho', 'ALTA', 'EM_ANDAMENTO', 30),
]

for titulo, desc, resp, prio, status, pct in plans:
    p_inicio = date(2026,2,1)
    p_fim = date(2026,7,30) if status != 'CONCLUIDO' else date(2026,4,15)
    ap, _ = ActionPlan.objects.update_or_create(
        company=company, titulo=titulo,
        defaults={
            'descricao': desc, 'responsavel': resp, 'prioridade': prio,
            'status': status, 'prazo_inicio': p_inicio, 'prazo_fim': p_fim,
            'percentual_conclusao': pct, 'created_by': admin,
            'data_conclusao': date(2026,4,10) if status == 'CONCLUIDO' else None,
            'risk_assessment': assess_objs[0] if 'Burnout' in titulo else None,
        }
    )
print(f"Planos de acao criados: {len(plans)}")
print("=== PARTE 1 CONCLUIDA ===")
