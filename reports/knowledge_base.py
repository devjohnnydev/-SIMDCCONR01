"""
==================================================================================
KNOWLEDGE BASE — SIMDCCONR01
==================================================================================
Banco de dados bibliográfico e rastreável para todos os 160 itens do questionário.

Regras de Negócio:
  🔴 R1 — Exclusividade Bibliográfica: Proibido usar autores fora dos anexos.
  🔴 R2 — Rastreabilidade Total: Todo item deve ter autor, obra, constructo.
  🔴 R3 — FDAC: Usar exclusivamente o e-book (Goulart, 2025).
  🔴 R4 — NR-01: Saída obrigatória para PGR/GRO + PCMSO.
  🔴 R5 — Hierarquia: Respondente → PCMSO → Departamento → Organização.
==================================================================================
"""

# =============================================================================
# CLASSIFICAÇÃO LIKERT (Tabela 3.3)
# =============================================================================
CLASSIFICATION_RANGES = [
    (1.0, 2.4, 'Crítico', 'critico'),
    (2.5, 3.4, 'Atenção', 'atencao'),
    (3.5, 4.2, 'Adequado', 'adequado'),
    (4.3, 5.0, 'Forte', 'forte'),
]


def classify_score(value):
    """Classifica um valor Likert (1-5) conforme a tabela de faixas."""
    if value is None:
        return 'Sem dados', 'sem_dados'
    val = float(value)
    for fmin, fmax, label, key in CLASSIFICATION_RANGES:
        if fmin <= val <= fmax:
            return label, key
    if val < 1.0:
        return 'Crítico', 'critico'
    return 'Forte', 'forte'


# =============================================================================
# REGRAS DE RISCO (Tabela 3.4)
# =============================================================================
RISK_RULES = {
    'critico': {
        'probabilidade': 'Alta',
        'impacto': 'Alto',
        'risco': 'Elevado',
        'acao_pgr': 'Intervenção imediata requerida. Incluir no PGR/GRO com prioridade máxima.',
    },
    'atencao': {
        'probabilidade': 'Média',
        'impacto': 'Médio',
        'risco': 'Moderado',
        'acao_pgr': 'Monitoramento contínuo e planejamento de ações corretivas no PGR/GRO.',
    },
    'adequado': {
        'probabilidade': 'Baixa',
        'impacto': 'Baixo',
        'risco': 'Baixo',
        'acao_pgr': 'Manutenção das práticas atuais com monitoramento periódico.',
    },
    'forte': {
        'probabilidade': 'Muito baixa',
        'impacto': 'Mínimo',
        'risco': 'Controlado',
        'acao_pgr': 'Ponto forte identificado. Manter e replicar boas práticas.',
    },
}


# =============================================================================
# REFERÊNCIAS BIBLIOGRÁFICAS (ABNT)
# =============================================================================
REFERENCES = {
    'litwin_stringer_1968': {
        'autor': 'Litwin, G. H.; Stringer, R. A.',
        'ano': 1968,
        'obra': 'Motivation and Organizational Climate',
        'referencia_abnt': (
            'LITWIN, G. H.; STRINGER, R. A. '
            'Motivation and Organizational Climate. '
            'Boston: Harvard University, 1968.'
        ),
    },
    'coda_2009': {
        'autor': 'Coda, R.',
        'ano': 2009,
        'obra': 'Pesquisa de Clima Organizacional e Gestão Estratégica de Recursos Humanos',
        'referencia_abnt': (
            'CODA, R. '
            'Pesquisa de Clima Organizacional e Gestão Estratégica '
            'de Recursos Humanos. In: BERGAMINI, C. W.; CODA, R. (Org.). '
            'Psicodinâmica da Vida Organizacional. 2. ed. São Paulo: Atlas, 2009.'
        ),
    },
    'goulart_2025': {
        'autor': 'Goulart, J. A. P.',
        'ano': 2025,
        'obra': 'Fairness, Disclosure, Accountability & Compliance: FDAC como Modelo de Cultura Organizacional',
        'referencia_abnt': (
            'GOULART, J. A. P. '
            'Fairness, Disclosure, Accountability & Compliance: '
            'FDAC como Modelo de Cultura Organizacional. '
            'São Paulo: [s.n.], 2025. E-book.'
        ),
    },
    'karasek_1979': {
        'autor': 'Karasek, R. A.',
        'ano': 1979,
        'obra': 'Job Demands, Job Decision Latitude, and Mental Strain',
        'referencia_abnt': (
            'KARASEK, R. A. '
            'Job Demands, Job Decision Latitude, and Mental Strain: '
            'Implications for Job Redesign. '
            'Administrative Science Quarterly, v. 24, n. 2, p. 285-308, 1979.'
        ),
    },
    'hackman_oldham_1976': {
        'autor': 'Hackman, J. R.; Oldham, G. R.',
        'ano': 1976,
        'obra': 'Motivation Through the Design of Work',
        'referencia_abnt': (
            'HACKMAN, J. R.; OLDHAM, G. R. '
            'Motivation Through the Design of Work: Test of a Theory. '
            'Organizational Behavior and Human Performance, v. 16, n. 2, p. 250-279, 1976.'
        ),
    },
    'nr01_2024': {
        'autor': 'Brasil. Ministério do Trabalho e Emprego',
        'ano': 2024,
        'obra': 'Norma Regulamentadora nº 01 — Disposições Gerais e Gerenciamento de Riscos Ocupacionais',
        'referencia_abnt': (
            'BRASIL. Ministério do Trabalho e Emprego. '
            'Norma Regulamentadora nº 01 — Disposições Gerais e '
            'Gerenciamento de Riscos Ocupacionais. Brasília, 2024.'
        ),
    },
    'nr12_2024': {
        'autor': 'Brasil. Ministério do Trabalho e Emprego',
        'ano': 2024,
        'obra': 'Norma Regulamentadora nº 12 — Segurança no Trabalho em Máquinas e Equipamentos',
        'referencia_abnt': (
            'BRASIL. Ministério do Trabalho e Emprego. '
            'Norma Regulamentadora nº 12 — Segurança no Trabalho em '
            'Máquinas e Equipamentos. Brasília, 2024.'
        ),
    },
    'nr17_2024': {
        'autor': 'Brasil. Ministério do Trabalho e Emprego',
        'ano': 2024,
        'obra': 'Norma Regulamentadora nº 17 — Ergonomia',
        'referencia_abnt': (
            'BRASIL. Ministério do Trabalho e Emprego. '
            'Norma Regulamentadora nº 17 — Ergonomia. Brasília, 2024.'
        ),
    },
}


# =============================================================================
# INTERPRETAÇÕES POR CLASSIFICAÇÃO E DIMENSÃO
# =============================================================================
# Mapeamento: (instrumento, dimensao, classificacao_key) → texto de interpretação
INTERPRETATIONS = {
    # ─── IMCO: Reconhecimento ──────────────────────────────────────────
    ('IMCO', 'Reconhecimento', 'critico'): (
        'Os resultados indicam percepção crítica quanto às práticas de reconhecimento. '
        'Há evidências de que o sistema de valorização não atende às expectativas dos '
        'colaboradores, gerando risco de desmotivação, rotatividade e queda de desempenho.'
    ),
    ('IMCO', 'Reconhecimento', 'atencao'): (
        'A percepção de reconhecimento encontra-se em nível de atenção. '
        'Embora existam práticas de valorização, estas não são percebidas como '
        'suficientes ou homogêneas, demandando ajustes.'
    ),
    ('IMCO', 'Reconhecimento', 'adequado'): (
        'As práticas de reconhecimento são percebidas de forma adequada. '
        'O sistema de valorização atende razoavelmente às expectativas, '
        'com espaço para aprimoramento contínuo.'
    ),
    ('IMCO', 'Reconhecimento', 'forte'): (
        'O reconhecimento é ponto forte da organização. '
        'As práticas de valorização são percebidas como homogêneas, justas e '
        'eficazes, contribuindo para o engajamento e retenção de talentos.'
    ),

    # ─── IMCO: Comprometimento ─────────────────────────────────────────
    ('IMCO', 'Comprometimento', 'critico'): (
        'O nível de comprometimento percebido é crítico. Há desengajamento '
        'significativo, com risco de absenteísmo, rotatividade e baixa produtividade. '
        'É necessária intervenção nas condições organizacionais que sustentam o vínculo.'
    ),
    ('IMCO', 'Comprometimento', 'atencao'): (
        'O comprometimento percebido está em nível de atenção, indicando '
        'fragilidades no vínculo organizacional que podem evoluir para desengajamento.'
    ),
    ('IMCO', 'Comprometimento', 'adequado'): (
        'O comprometimento está adequado, com colaboradores demonstrando vínculo '
        'razoável com a organização e suas metas.'
    ),
    ('IMCO', 'Comprometimento', 'forte'): (
        'O comprometimento é forte, evidenciando vínculo sólido, orgulho de pertencimento '
        'e fidelidade à organização.'
    ),

    # ─── IMCO: Progresso Profissional ──────────────────────────────────
    ('IMCO', 'Progresso Profissional', 'critico'): (
        'A percepção de progresso profissional é crítica. Os colaboradores não '
        'vislumbram oportunidades de crescimento, o que impacta diretamente a motivação e retenção.'
    ),
    ('IMCO', 'Progresso Profissional', 'atencao'): (
        'O progresso profissional percebido está em atenção. Há lacunas nas '
        'oportunidades de desenvolvimento que devem ser endereçadas.'
    ),
    ('IMCO', 'Progresso Profissional', 'adequado'): (
        'As oportunidades de progresso profissional são percebidas como adequadas, '
        'com acesso razoável a crescimento e desenvolvimento.'
    ),
    ('IMCO', 'Progresso Profissional', 'forte'): (
        'O progresso profissional é ponto forte. Há excelentes oportunidades de '
        'crescimento percebidas pelos colaboradores.'
    ),

    # ─── IMCO: Estilo de Liderança ─────────────────────────────────────
    ('IMCO', 'Estilo de Liderança', 'critico'): (
        'A liderança é percebida de forma crítica. Há indícios de gestão '
        'inadequada, falta de suporte e possível comprometimento da saúde '
        'psicossocial da equipe, configurando fator de risco conforme Karasek (1979).'
    ),
    ('IMCO', 'Estilo de Liderança', 'atencao'): (
        'O estilo de liderança está em nível de atenção. Há aspectos que '
        'precisam de desenvolvimento, especialmente no suporte e coerência gerencial.'
    ),
    ('IMCO', 'Estilo de Liderança', 'adequado'): (
        'A liderança é percebida como adequada, com acessibilidade e respeito razoáveis.'
    ),
    ('IMCO', 'Estilo de Liderança', 'forte'): (
        'A liderança é ponto forte. Há coerência entre discurso e prática, '
        'acessibilidade, suporte e valorização das contribuições da equipe.'
    ),

    # ─── IMCO: Equipe ──────────────────────────────────────────────────
    ('IMCO', 'Equipe', 'critico'): (
        'O trabalho em equipe apresenta resultado crítico. Há fragmentação, '
        'protecionismo e possíveis conflitos interpessoais que comprometem o desempenho coletivo.'
    ),
    ('IMCO', 'Equipe', 'atencao'): (
        'O trabalho em equipe está em nível de atenção, com fragilidades na união e no apoio mútuo.'
    ),
    ('IMCO', 'Equipe', 'adequado'): (
        'O trabalho em equipe é adequado, com cooperação e apoio mútuo razoáveis.'
    ),
    ('IMCO', 'Equipe', 'forte'): (
        'O trabalho em equipe é forte, com excelente união, apoio mútuo e fluxo de trabalho colaborativo.'
    ),

    # ─── IMCO: Competição ──────────────────────────────────────────────
    ('IMCO', 'Competição', 'critico'): (
        'A competição interna é percebida como nociva, comprometendo a harmonia e o desempenho.'
    ),
    ('IMCO', 'Competição', 'atencao'): (
        'A competição está em nível de atenção, podendo evoluir para conflitos caso não seja moderada.'
    ),
    ('IMCO', 'Competição', 'adequado'): (
        'A competição é percebida como sadia, estimulando criatividade sem comprometer relações.'
    ),
    ('IMCO', 'Competição', 'forte'): (
        'A competição é saudável e harmoniosa, contribuindo positivamente para o desempenho.'
    ),

    # ─── IMCO: Clareza Organizacional ──────────────────────────────────
    ('IMCO', 'Clareza Organizacional', 'critico'): (
        'Há percepção crítica sobre a clareza organizacional. Objetivos e estratégias '
        'não são comunicados adequadamente, gerando desalinhamento e ineficiência.'
    ),
    ('IMCO', 'Clareza Organizacional', 'atencao'): (
        'A clareza organizacional está em atenção. Há lacunas na comunicação de '
        'estratégias e desalinhamento parcial entre discurso e prática gerencial.'
    ),
    ('IMCO', 'Clareza Organizacional', 'adequado'): (
        'A clareza organizacional é adequada, com comunicação razoável de objetivos e estratégias.'
    ),
    ('IMCO', 'Clareza Organizacional', 'forte'): (
        'Excelente clareza organizacional. Objetivos, metas e estratégias são bem comunicados.'
    ),

    # ─── IMCO: Comunicação ─────────────────────────────────────────────
    ('IMCO', 'Comunicação', 'critico'): (
        'A comunicação organizacional é percebida como crítica. Informações não fluem '
        'adequadamente, comprometendo a execução do trabalho e a confiança institucional.'
    ),
    ('IMCO', 'Comunicação', 'atencao'): (
        'A comunicação está em nível de atenção, com ruídos e assimetrias informacionais.'
    ),
    ('IMCO', 'Comunicação', 'adequado'): (
        'A comunicação é adequada, com canais razoavelmente eficientes.'
    ),
    ('IMCO', 'Comunicação', 'forte'): (
        'A comunicação é forte. Canais são ágeis, transparentes e de mão dupla.'
    ),

    # ─── IMCO: Regras e Estrutura ──────────────────────────────────────
    ('IMCO', 'Regras e Estrutura', 'critico'): (
        'A estrutura e as regras organizacionais são percebidas como críticas. '
        'Há ambiguidade de papéis, sobreposição de atribuições e rigidez excessiva.'
    ),
    ('IMCO', 'Regras e Estrutura', 'atencao'): (
        'A estrutura organizacional está em atenção, com necessidade de ajustes em '
        'divisão de papéis e flexibilidade.'
    ),
    ('IMCO', 'Regras e Estrutura', 'adequado'): (
        'A estrutura e regras são adequadas, com divisão razoável de papéis e abertura a sugestões.'
    ),
    ('IMCO', 'Regras e Estrutura', 'forte'): (
        'A estrutura organizacional é forte, consistente com os objetivos e com excelente flexibilidade.'
    ),

    # ─── IMCO: Política Salarial ───────────────────────────────────────
    ('IMCO', 'Política Salarial', 'critico'): (
        'A política salarial e de benefícios é percebida como crítica, sendo fator '
        'de insatisfação e risco de rotatividade.'
    ),
    ('IMCO', 'Política Salarial', 'atencao'): (
        'A política salarial está em atenção, com percepção de desbalanceamento entre '
        'compensação e contribuição.'
    ),
    ('IMCO', 'Política Salarial', 'adequado'): (
        'A política salarial é adequada, sem interferência significativa na satisfação.'
    ),
    ('IMCO', 'Política Salarial', 'forte'): (
        'A política salarial é forte, com benefícios amplos e remuneração percebida como justa.'
    ),

    # ─── IMCO: Salário ─────────────────────────────────────────────────
    ('IMCO', 'Salário', 'critico'): (
        'A percepção salarial é crítica. Colaboradores percebem injustiça remuneratória.'
    ),
    ('IMCO', 'Salário', 'atencao'): (
        'O salário está em atenção, com percepção de incompatibilidade parcial.'
    ),
    ('IMCO', 'Salário', 'adequado'): (
        'O salário é percebido como adequado e compatível com o desempenho.'
    ),
    ('IMCO', 'Salário', 'forte'): (
        'A percepção salarial é forte, com reconhecimento de justiça remuneratória.'
    ),

    # ─── IMCO: RH ──────────────────────────────────────────────────────
    ('IMCO', 'Gestão de RH', 'critico'): (
        'A gestão de Recursos Humanos é percebida como crítica. Há deficiências '
        'em avaliação de desempenho, justiça e suporte emocional.'
    ),
    ('IMCO', 'Gestão de RH', 'atencao'): (
        'A gestão de RH está em atenção, com necessidade de aprimoramento em práticas e instrumentos.'
    ),
    ('IMCO', 'Gestão de RH', 'adequado'): (
        'A gestão de RH é adequada, com práticas razoavelmente eficientes.'
    ),
    ('IMCO', 'Gestão de RH', 'forte'): (
        'A gestão de RH é forte, com instrumentos eficazes e preocupação com justiça e ética.'
    ),

    # ─── IMCO: Carreira ────────────────────────────────────────────────
    ('IMCO', 'Carreira', 'critico'): (
        'A percepção de carreira é crítica. Não há horizonte profissional claro.'
    ),
    ('IMCO', 'Carreira', 'atencao'): (
        'A percepção de carreira está em atenção, com lacunas nas oportunidades de desenvolvimento.'
    ),
    ('IMCO', 'Carreira', 'adequado'): (
        'A carreira é percebida como adequada, com boas oportunidades de competências.'
    ),
    ('IMCO', 'Carreira', 'forte'): (
        'A percepção de carreira é forte, com horizonte profissional claro e oportunidades visíveis.'
    ),

    # ─── IMCO: Treinamento ─────────────────────────────────────────────
    ('IMCO', 'Treinamento', 'critico'): (
        'O treinamento é percebido como crítico, com falta de investimento na formação profissional.'
    ),
    ('IMCO', 'Treinamento', 'atencao'): (
        'O treinamento está em atenção, com necessidade de ampliar oportunidades de capacitação.'
    ),
    ('IMCO', 'Treinamento', 'adequado'): (
        'O treinamento é adequado, com apoio razoável para capacitação profissional.'
    ),
    ('IMCO', 'Treinamento', 'forte'): (
        'O treinamento é forte, com excelente valorização e apoio à formação profissional.'
    ),

    # ─── IMCO: Conteúdo do Trabalho ────────────────────────────────────
    ('IMCO', 'Conteúdo do Trabalho', 'critico'): (
        'O conteúdo do trabalho é percebido como crítico. Há desalinhamento entre '
        'tarefas e expectativas, com risco de desmotivação.'
    ),
    ('IMCO', 'Conteúdo do Trabalho', 'atencao'): (
        'O conteúdo do trabalho está em atenção, com necessidade de enriquecimento das tarefas.'
    ),
    ('IMCO', 'Conteúdo do Trabalho', 'adequado'): (
        'O conteúdo do trabalho é adequado, com tarefas interessantes e desafiantes.'
    ),
    ('IMCO', 'Conteúdo do Trabalho', 'forte'): (
        'O conteúdo do trabalho é forte, com excelente aproveitamento de habilidades e potencial.'
    ),

    # ─── IMCO: Volume de Trabalho (inclui NR-01, NR-17) ───────────────
    ('IMCO', 'Volume de Trabalho', 'critico'): (
        'O volume de trabalho é percebido como crítico, configurando risco psicossocial '
        'por sobrecarga conforme modelo Demanda-Controle de Karasek (1979). '
        'Há comprometimento do equilíbrio vida-trabalho e risco ergonômico conforme NR-17.'
    ),
    ('IMCO', 'Volume de Trabalho', 'atencao'): (
        'O volume de trabalho está em atenção. Há percepção de sobrecarga parcial '
        'que pode evoluir para risco psicossocial.'
    ),
    ('IMCO', 'Volume de Trabalho', 'adequado'): (
        'O volume de trabalho é adequado, com dimensionamento razoável.'
    ),
    ('IMCO', 'Volume de Trabalho', 'forte'): (
        'O volume de trabalho é forte, com excelente dimensionamento e equilíbrio.'
    ),

    # ─── IMCO: Ergonomia (NR-17) ──────────────────────────────────────
    ('IMCO', 'Ergonomia', 'critico'): (
        'As condições ergonômicas são percebidas como críticas. Há risco de '
        'sobrecarga cognitiva e inadequação organizacional conforme NR-17 e modelo '
        'de Hackman & Oldham (1976). Intervenção imediata requerida.'
    ),
    ('IMCO', 'Ergonomia', 'atencao'): (
        'As condições ergonômicas estão em atenção, com necessidade de ajustes '
        'em postura, pausas e carga cognitiva conforme NR-17.'
    ),
    ('IMCO', 'Ergonomia', 'adequado'): (
        'As condições ergonômicas são adequadas, com ambiente razoavelmente compatível com NR-17.'
    ),
    ('IMCO', 'Ergonomia', 'forte'): (
        'As condições ergonômicas são fortes, com excelente adequação ao NR-17.'
    ),

    # ─── IMCO: NR-12 (Segurança) ──────────────────────────────────────
    ('IMCO', 'Segurança NR-12', 'critico'): (
        'A percepção de segurança em máquinas e equipamentos é crítica. Há risco '
        'de falha comportamental e percepção de risco conforme NR-12.'
    ),
    ('IMCO', 'Segurança NR-12', 'atencao'): (
        'A segurança em máquinas e equipamentos está em atenção, com necessidade de '
        'reforço de treinamento e padronização de procedimentos conforme NR-12.'
    ),
    ('IMCO', 'Segurança NR-12', 'adequado'): (
        'A segurança é adequada, com dispositivos de proteção percebidos como funcionais.'
    ),
    ('IMCO', 'Segurança NR-12', 'forte'): (
        'A segurança é forte, com excelente percepção de proteção e ergonomia de máquinas.'
    ),

    # ─── IMCO: NR-17 Ampliado ─────────────────────────────────────────
    ('IMCO', 'Ergonomia Ampliada NR-17', 'critico'): (
        'As condições ergonômicas ampliadas são críticas. Há sobrecarga cognitiva, '
        'monotonia, exaustão e inadequação do posto de trabalho conforme NR-17 e '
        'Hackman & Oldham (1976).'
    ),
    ('IMCO', 'Ergonomia Ampliada NR-17', 'atencao'): (
        'As condições ergonômicas ampliadas estão em atenção, com necessidade de '
        'redesenho do trabalho e ajuste de pausas.'
    ),
    ('IMCO', 'Ergonomia Ampliada NR-17', 'adequado'): (
        'As condições ergonômicas ampliadas são adequadas.'
    ),
    ('IMCO', 'Ergonomia Ampliada NR-17', 'forte'): (
        'As condições ergonômicas ampliadas são fortes, com excelente organização do trabalho.'
    ),

    # ─── FDAC: Cultura Organizacional ──────────────────────────────────
    ('FDAC', 'Fairness', 'critico'): (
        'A dimensão de Fairness (equidade) é crítica. Há percepção de injustiça '
        'nas práticas de reconhecimento, remuneração e progressão, conforme modelo '
        'FDAC (Goulart, 2025). Impacto direto na governança e confiança organizacional.'
    ),
    ('FDAC', 'Fairness', 'atencao'): (
        'A equidade (Fairness) está em atenção, com percepção de desequilíbrios pontuais.'
    ),
    ('FDAC', 'Fairness', 'adequado'): (
        'A equidade é adequada, com práticas razoavelmente justas e equitativas.'
    ),
    ('FDAC', 'Fairness', 'forte'): (
        'A equidade é ponto forte, com excelente percepção de justiça e imparcialidade.'
    ),

    ('FDAC', 'Disclosure', 'critico'): (
        'A transparência (Disclosure) é crítica. Há falta de acesso a informações '
        'relevantes e canais ineficazes, conforme FDAC (Goulart, 2025).'
    ),
    ('FDAC', 'Disclosure', 'atencao'): (
        'A transparência está em atenção, com lacunas na comunicação de informações estratégicas.'
    ),
    ('FDAC', 'Disclosure', 'adequado'): (
        'A transparência é adequada, com boa comunicação de informações relevantes.'
    ),
    ('FDAC', 'Disclosure', 'forte'): (
        'A transparência é forte, com excelente acesso a informações e canais eficazes.'
    ),

    ('FDAC', 'Accountability', 'critico'): (
        'A responsabilização (Accountability) é crítica. Há falta de clareza nos papéis '
        'e responsabilidades, conforme FDAC (Goulart, 2025).'
    ),
    ('FDAC', 'Accountability', 'atencao'): (
        'A responsabilização está em atenção, com necessidade de definição mais precisa de papéis.'
    ),
    ('FDAC', 'Accountability', 'adequado'): (
        'A responsabilização é adequada, com papéis razoavelmente definidos.'
    ),
    ('FDAC', 'Accountability', 'forte'): (
        'A responsabilização é forte, com metas claras e responsabilidade compartilhada.'
    ),

    ('FDAC', 'Compliance', 'critico'): (
        'O compliance é crítico. Há falhas na aderência a normas éticas e legais, '
        'conforme FDAC (Goulart, 2025). Risco jurídico e reputacional elevado.'
    ),
    ('FDAC', 'Compliance', 'atencao'): (
        'O compliance está em atenção, com necessidade de reforço em treinamento ético e regulatório.'
    ),
    ('FDAC', 'Compliance', 'adequado'): (
        'O compliance é adequado, com aderência razoável a normas éticas e legais.'
    ),
    ('FDAC', 'Compliance', 'forte'): (
        'O compliance é forte, com excelente aderência a normas éticas e legais.'
    ),

    # ─── NR-01: Fatores de Risco Psicossocial ─────────────────────────
    ('NR-01', 'Saúde Neurológica', 'critico'): (
        'Identificados sinais neurológicos relevantes que demandam encaminhamento '
        'médico ocupacional imediato conforme NR-01 e PCMSO.'
    ),
    ('NR-01', 'Saúde Neurológica', 'atencao'): (
        'Sinais neurológicos em atenção. Recomendado acompanhamento clínico ocupacional.'
    ),

    ('NR-01', 'Histórico Clínico', 'critico'): (
        'Histórico clínico relevante identificado, com possível impacto na '
        'capacidade laboral. Encaminhamento ao PCMSO requerido.'
    ),
    ('NR-01', 'Histórico Clínico', 'atencao'): (
        'Histórico clínico em atenção. Monitoramento periódico recomendado.'
    ),

    ('NR-01', 'Desempenho Cognitivo', 'critico'): (
        'O desempenho cognitivo é crítico, com esquecimentos frequentes, dificuldade '
        'de planejamento e atraso em decisões. Conforme Karasek (1979), há sobrecarga '
        'cognitiva que demanda intervenção.'
    ),
    ('NR-01', 'Desempenho Cognitivo', 'atencao'): (
        'O desempenho cognitivo está em atenção, com sinais de sobrecarga que merecem monitoramento.'
    ),
    ('NR-01', 'Desempenho Cognitivo', 'adequado'): (
        'O desempenho cognitivo é adequado, sem sinais relevantes de comprometimento.'
    ),
    ('NR-01', 'Desempenho Cognitivo', 'forte'): (
        'O desempenho cognitivo é forte, sem sinais de sobrecarga.'
    ),

    ('NR-01', 'Condições Laborais', 'critico'): (
        'As condições laborais apresentam fatores críticos de risco psicossocial, '
        'incluindo inadequação de sono, jornada excessiva e/ou exposição a assédio.'
    ),
    ('NR-01', 'Condições Laborais', 'atencao'): (
        'As condições laborais estão em atenção, com fatores que demandam monitoramento.'
    ),

    ('NR-01', 'Desempenho Funcional', 'critico'): (
        'O desempenho funcional é crítico, com indicadores de absenteísmo, '
        'presenteísmo e queda de produtividade.'
    ),
    ('NR-01', 'Desempenho Funcional', 'atencao'): (
        'O desempenho funcional está em atenção, com sinais de comprometimento parcial.'
    ),
    ('NR-01', 'Desempenho Funcional', 'adequado'): (
        'O desempenho funcional é adequado.'
    ),
    ('NR-01', 'Desempenho Funcional', 'forte'): (
        'O desempenho funcional é forte.'
    ),

    ('NR-01', 'Uso de Substâncias', 'critico'): (
        'Identificado padrão de uso de substâncias que configura risco de dependência '
        'e comprometimento da segurança ocupacional. Encaminhamento médico obrigatório.'
    ),
    ('NR-01', 'Uso de Substâncias', 'atencao'): (
        'Uso de substâncias em atenção. Monitoramento e orientação recomendados.'
    ),
    ('NR-01', 'Uso de Substâncias', 'adequado'): (
        'Sem indicadores relevantes de uso problemático de substâncias.'
    ),
    ('NR-01', 'Uso de Substâncias', 'forte'): (
        'Sem indicadores de uso problemático de substâncias.'
    ),
}


# =============================================================================
# RECOMENDAÇÕES POR CLASSIFICAÇÃO E DIMENSÃO
# =============================================================================
RECOMMENDATIONS = {
    # ─── Recomendações por tipo: respondente, organização, pcmso ──────

    # IMCO — Genéricas por classificação
    'respondente': {
        'critico': (
            'Recomenda-se acompanhamento imediato com foco em suporte emocional, '
            'readequação de condições de trabalho e, quando indicado, encaminhamento '
            'para avaliação clínica ocupacional.'
        ),
        'atencao': (
            'Recomenda-se monitoramento periódico e ações preventivas para evitar '
            'evolução do cenário para nível crítico.'
        ),
        'adequado': (
            'Manutenção das condições atuais com acompanhamento periódico.'
        ),
        'forte': (
            'Manutenção e valorização das práticas e condições que sustentam este resultado.'
        ),
    },
    'organizacao': {
        'critico': (
            '1. Eliminação: Redesenho organizacional do trabalho.\n'
            '2. Substituição: Ajuste de processos críticos.\n'
            '3. Engenharia: Reestruturação de fluxos e carga de trabalho.\n'
            '4. Administrativas: Revisão de metas, redefinição de papéis, capacitação de liderança.\n'
            '5. Monitoramento: Indicadores contínuos via clima organizacional.'
        ),
        'atencao': (
            '1. Administrativas: Revisão de metas e processos.\n'
            '2. Capacitação: Treinamento de liderança e gestão de pessoas.\n'
            '3. Monitoramento: Acompanhamento trimestral de indicadores.'
        ),
        'adequado': (
            '1. Manutenção das práticas atuais.\n'
            '2. Monitoramento semestral de indicadores.'
        ),
        'forte': (
            '1. Reconhecimento e disseminação das boas práticas.\n'
            '2. Monitoramento anual de indicadores.'
        ),
    },
    'pcmso': {
        'critico': (
            '1. Monitoramento periódico: Avaliação clínica ocupacional regular.\n'
            '2. Acompanhamento: Foco em sinais de estresse ocupacional.\n'
            '3. Encaminhamento: Avaliação especializada quando aplicável.\n'
            '4. Registro: Inclusão no PCMSO e prontuário ocupacional.'
        ),
        'atencao': (
            '1. Monitoramento periódico: Avaliação clínica ocupacional semestral.\n'
            '2. Acompanhamento: Atenção a sinais de sobrecarga.\n'
            '3. Registro: Inclusão no PCMSO.'
        ),
        'adequado': (
            '1. Monitoramento periódico: Avaliação clínica ocupacional anual.\n'
            '2. Registro: Inclusão no PCMSO.'
        ),
        'forte': (
            '1. Manutenção dos indicadores positivos.\n'
            '2. Registro: Inclusão no PCMSO.'
        ),
    },
}


# =============================================================================
# MAPEAMENTO: ORDEM DA QUESTÃO → METADADOS
# =============================================================================
# Cada item do questionário (pela sua ordem/order no FormQuestion) é mapeado
# para seus metadados de instrumento, dimensão, vetor, referência e constructo.

ITEM_METADATA = {}


def _register_items(order_start, order_end, instrumento, vetor, dimensao, ref_key, constructo):
    """Helper para registrar uma faixa de itens com mesmos metadados."""
    ref = REFERENCES[ref_key]
    for order in range(order_start, order_end + 1):
        ITEM_METADATA[order] = {
            'instrumento': instrumento,
            'vetor': vetor,
            'dimensao': dimensao,
            'autor': ref['autor'],
            'ano': ref['ano'],
            'obra': ref['obra'],
            'constructo': constructo,
            'referencia_abnt': ref['referencia_abnt'],
            'ref_key': ref_key,
        }


# ─── IMCO: Motivação ─────────────────────────────────────────────────
_register_items(1, 7, 'IMCO', 'Motivação', 'Reconhecimento', 'litwin_stringer_1968',
    'o clima organizacional e os sistemas de reconhecimento impactam diretamente '
    'a motivação, o desempenho e a satisfação dos colaboradores')

_register_items(8, 13, 'IMCO', 'Motivação', 'Comprometimento', 'coda_2009',
    'o comprometimento organizacional reflete o vínculo afetivo e instrumental '
    'do colaborador com a organização, influenciando diretamente a produtividade e retenção')

_register_items(14, 18, 'IMCO', 'Motivação', 'Progresso Profissional', 'coda_2009',
    'as oportunidades de crescimento profissional percebidas pelos colaboradores '
    'são determinantes para a motivação e a retenção de talentos')

# ─── IMCO: Liderança ─────────────────────────────────────────────────
_register_items(19, 29, 'IMCO', 'Liderança', 'Estilo de Liderança', 'litwin_stringer_1968',
    'o estilo de liderança influencia o clima organizacional, a percepção de suporte '
    'e a satisfação dos colaboradores com o ambiente de trabalho')

_register_items(30, 36, 'IMCO', 'Liderança', 'Equipe', 'litwin_stringer_1968',
    'a qualidade das relações de equipe, incluindo união, apoio mútuo e '
    'ausência de protecionismo, é componente fundamental do clima organizacional')

_register_items(37, 39, 'IMCO', 'Liderança', 'Competição', 'litwin_stringer_1968',
    'a competição sadia entre pessoas e grupos estimula a criatividade e melhora '
    'o desempenho, desde que não comprometa a harmonia do ambiente')

# ─── IMCO: Filosofia de Gestão ────────────────────────────────────────
_register_items(40, 47, 'IMCO', 'Filosofia de Gestão', 'Clareza Organizacional', 'coda_2009',
    'a clareza sobre objetivos, metas e valores organizacionais é fundamental '
    'para o alinhamento estratégico e a percepção positiva do clima')

_register_items(48, 57, 'IMCO', 'Filosofia de Gestão', 'Comunicação', 'coda_2009',
    'a comunicação organizacional eficaz, ágil e transparente é condição para '
    'o bom funcionamento da organização e para a satisfação dos colaboradores')

_register_items(58, 62, 'IMCO', 'Filosofia de Gestão', 'Regras e Estrutura', 'coda_2009',
    'a estrutura organizacional, a divisão de papéis e a flexibilidade para '
    'sugestões impactam a eficácia e a satisfação dos colaboradores')

# ─── IMCO: Gestão de Pessoas ──────────────────────────────────────────
_register_items(63, 69, 'IMCO', 'Gestão de Pessoas', 'Política Salarial', 'coda_2009',
    'o sistema de compensação (salário + benefícios) é determinante para a '
    'satisfação e retenção dos colaboradores na organização')

_register_items(70, 73, 'IMCO', 'Gestão de Pessoas', 'Salário', 'coda_2009',
    'a percepção de justiça salarial, refletida na adequação entre contribuição '
    'e retribuição, impacta a motivação e o comprometimento')

_register_items(74, 78, 'IMCO', 'Gestão de Pessoas', 'Gestão de RH', 'coda_2009',
    'as práticas de gestão de recursos humanos, incluindo avaliação de desempenho, '
    'justiça e suporte, determinam a qualidade do ambiente de trabalho')

_register_items(79, 83, 'IMCO', 'Gestão de Pessoas', 'Carreira', 'coda_2009',
    'as oportunidades de carreira e o horizonte profissional percebidos '
    'são determinantes para a motivação e a permanência na organização')

_register_items(84, 86, 'IMCO', 'Gestão de Pessoas', 'Treinamento', 'coda_2009',
    'o investimento em treinamento e desenvolvimento profissional é fator '
    'central na formação de competências e na retenção de talentos')

# ─── IMCO: Natureza do Trabalho ───────────────────────────────────────
_register_items(87, 91, 'IMCO', 'Natureza do Trabalho', 'Conteúdo do Trabalho', 'hackman_oldham_1976',
    'o conteúdo do trabalho, incluindo desafio, autonomia e aproveitamento '
    'de competências, é determinante para a motivação intrínseca')

_register_items(92, 100, 'IMCO', 'Natureza do Trabalho', 'Volume de Trabalho', 'karasek_1979',
    'o volume e a organização do trabalho impactam diretamente a saúde '
    'psicossocial, conforme o modelo Demanda-Controle, podendo gerar '
    'estresse e adoecimento quando excessivos')

# ─── IMCO: Ergonomia NR-17 ────────────────────────────────────────────
_register_items(101, 106, 'IMCO', 'Natureza do Trabalho', 'Ergonomia', 'hackman_oldham_1976',
    'as condições ergonômicas do trabalho, incluindo aspectos físicos e cognitivos, '
    'determinam o conforto, a segurança e a produtividade do trabalhador, '
    'conforme preconizado pela NR-17')

# ─── IMCO: NR-12 ──────────────────────────────────────────────────────
_register_items(107, 108, 'IMCO', 'Natureza do Trabalho', 'Segurança NR-12', 'nr12_2024',
    'a percepção de segurança em máquinas e equipamentos, incluindo dispositivos '
    'de proteção e interface ergonômica, é condição para a integridade física '
    'e psicológica do trabalhador conforme NR-12')

# ─── IMCO: NR-17 Ampliado ─────────────────────────────────────────────
_register_items(109, 114, 'IMCO', 'Natureza do Trabalho', 'Ergonomia Ampliada NR-17', 'nr17_2024',
    'a organização do trabalho, incluindo controle sobre ritmo, pausas, '
    'exigências cognitivas e monotonia, impacta a saúde e o desempenho '
    'do trabalhador conforme NR-17')

# ─── FDAC: Cultura Organizacional ─────────────────────────────────────
_register_items(115, 117, 'FDAC', 'Cultura', 'Fairness', 'goulart_2025',
    'a dimensão de Fairness (equidade) estabelece que as práticas de '
    'reconhecimento, remuneração e progressão devem ser justas e equitativas, '
    'como fundamento da cultura organizacional saudável')

_register_items(118, 120, 'FDAC', 'Cultura', 'Disclosure', 'goulart_2025',
    'a dimensão de Disclosure (transparência) estabelece que a comunicação '
    'de objetivos estratégicos e o acesso a informações relevantes são '
    'pilares da confiança organizacional')

_register_items(121, 123, 'FDAC', 'Cultura', 'Accountability', 'goulart_2025',
    'a dimensão de Accountability (responsabilização) preconiza clareza de '
    'papéis, responsabilidade compartilhada e metas bem definidas como '
    'base para a eficácia organizacional')

_register_items(124, 126, 'FDAC', 'Cultura', 'Compliance', 'goulart_2025',
    'a dimensão de Compliance estabelece a necessária aderência a normas '
    'éticas e legais, incluindo treinamento regulatório e integridade, '
    'como condição para a sustentabilidade organizacional')

# ─── NR-01: Bloco K — Saúde Neurológica ───────────────────────────────
_register_items(127, 134, 'NR-01', 'Risco Psicossocial', 'Saúde Neurológica', 'karasek_1979',
    'os indicadores neurológicos percebidos podem estar associados a fatores '
    'de risco psicossocial e sobrecarga no ambiente de trabalho')

# ─── NR-01: Bloco L — Histórico Clínico ───────────────────────────────
_register_items(135, 142, 'NR-01', 'Risco Psicossocial', 'Histórico Clínico', 'nr01_2024',
    'o histórico clínico do trabalhador constitui fator relevante para o '
    'gerenciamento de riscos ocupacionais conforme NR-01')

# ─── NR-01: Bloco M — Desempenho Cognitivo ────────────────────────────
_register_items(143, 150, 'NR-01', 'Risco Psicossocial', 'Desempenho Cognitivo', 'karasek_1979',
    'o desempenho cognitivo, incluindo memória, atenção e planejamento, '
    'pode ser impactado por condições de trabalho com alta demanda e baixo '
    'controle conforme o modelo Demanda-Controle')

# ─── NR-01: Bloco N — Condições Laborais ──────────────────────────────
_register_items(151, 158, 'NR-01', 'Risco Psicossocial', 'Condições Laborais', 'nr01_2024',
    'as condições laborais, incluindo sono, jornada, assédio e suporte, '
    'constituem fatores de risco psicossocial conforme NR-01')

# ─── NR-01: Bloco O — Desempenho Funcional ────────────────────────────
_register_items(159, 164, 'NR-01', 'Risco Psicossocial', 'Desempenho Funcional', 'karasek_1979',
    'indicadores de desempenho funcional, como absenteísmo, queda de '
    'produtividade e rotatividade, refletem o impacto dos fatores '
    'psicossociais sobre a capacidade laboral')

# ─── NR-01: Blocos P+Q — Uso de Substâncias ──────────────────────────
_register_items(165, 171, 'NR-01', 'Risco Psicossocial', 'Uso de Substâncias', 'nr01_2024',
    'o uso de substâncias psicoativas pode estar associado a mecanismos '
    'de enfrentamento de estresse ocupacional, configurando risco '
    'para a segurança e saúde do trabalhador')


# =============================================================================
# FUNÇÕES AUXILIARES
# =============================================================================

def get_item_metadata(order):
    """Retorna os metadados de um item pelo seu número de ordem."""
    return ITEM_METADATA.get(order, None)


def get_interpretation(instrumento, dimensao, classificacao_key):
    """Retorna a interpretação para uma combinação instrumento/dimensão/classificação."""
    key = (instrumento, dimensao, classificacao_key)
    return INTERPRETATIONS.get(key, (
        f'O resultado para a dimensão {dimensao} do instrumento {instrumento} '
        f'encontra-se em nível {classificacao_key}.'
    ))


def get_recommendation(tipo, classificacao_key):
    """Retorna a recomendação para um tipo (respondente/organizacao/pcmso) e classificação."""
    tipo_recs = RECOMMENDATIONS.get(tipo, RECOMMENDATIONS['respondente'])
    return tipo_recs.get(classificacao_key, 'Monitoramento recomendado.')


def get_all_references():
    """Retorna todas as referências bibliográficas únicas para lista de referências ABNT."""
    refs = set()
    for order, meta in ITEM_METADATA.items():
        refs.add(meta['referencia_abnt'])
    return sorted(refs)


def validate_coverage():
    """
    Valida que todos os 160 itens (ordem 1 a 171) estão mapeados.
    Retorna (is_valid, missing_orders).
    """
    expected = set(range(1, 172))
    covered = set(ITEM_METADATA.keys())
    missing = expected - covered
    return len(missing) == 0, sorted(missing)
