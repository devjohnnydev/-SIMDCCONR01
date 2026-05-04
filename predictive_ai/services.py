"""
Motor de IA Preditiva — Análise de tendências e geração de sugestões.
Detecta padrões negativos no histórico e prevê riscos crescentes.
"""
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta


def analyze_sector_trends(company):
    """
    Analisa tendência de cada setor nos últimos 3+ snapshots.
    Se detectar queda linear, gera alerta preditivo.
    Returns: list de alertas criados.
    """
    from evolution.models import EvolutionSnapshot
    from .models import PredictiveAlert

    snapshots = EvolutionSnapshot.objects.filter(
        company=company
    ).order_by('snapshot_date')[:12]

    if snapshots.count() < 2:
        return []

    # Agrupar sector_scores por snapshot
    sector_history = {}
    for snap in snapshots:
        if snap.sector_scores:
            for sector, score in snap.sector_scores.items():
                if sector not in sector_history:
                    sector_history[sector] = []
                sector_history[sector].append({
                    'date': snap.snapshot_date.isoformat(),
                    'score': float(score),
                })

    alerts_created = []
    for sector, history in sector_history.items():
        if len(history) < 2:
            continue

        # Análise de tendência simples (últimos 3 pontos)
        recent = history[-3:] if len(history) >= 3 else history
        scores = [h['score'] for h in recent]

        # Verificar se há queda consecutiva
        is_declining = all(
            scores[i] > scores[i + 1]
            for i in range(len(scores) - 1)
        )

        if is_declining and len(scores) >= 2:
            # Calcular taxa de declínio
            decline_rate = scores[0] - scores[-1]
            # Projetar score futuro
            avg_decline = decline_rate / (len(scores) - 1)
            projected = scores[-1] - avg_decline

            # Determinar confiança
            if len(scores) >= 3 and decline_rate > 0.5:
                confidence = 'HIGH'
            elif decline_rate > 0.3:
                confidence = 'MEDIUM'
            else:
                confidence = 'LOW'

            # Verificar se já existe alerta recente para este setor
            existing = PredictiveAlert.objects.filter(
                company=company,
                trend_type='SECTOR_DECLINE',
                setor=sector,
                is_acknowledged=False,
                created_at__gte=timezone.now() - timedelta(days=30)
            ).exists()

            if not existing:
                alert = PredictiveAlert.objects.create(
                    company=company,
                    trend_type='SECTOR_DECLINE',
                    confidence=confidence,
                    titulo=f'Setor "{sector}" em tendência de queda',
                    descricao=(
                        f'O setor "{sector}" apresentou queda consecutiva nos últimos '
                        f'{len(scores)} laudos. Score atual: {scores[-1]:.2f}, '
                        f'Score anterior: {scores[0]:.2f}. '
                        f'Declínio de {decline_rate:.2f} pontos.'
                    ),
                    recomendacao=(
                        f'Recomenda-se realizar nova pesquisa focada no setor "{sector}" '
                        f'para identificar causas específicas da queda. Considerar: '
                        f'entrevistas individuais, revisão de condições ergonômicas (NR-17), '
                        f'e avaliação de riscos psicossociais (NR-1 GRO).'
                    ),
                    setor=sector,
                    score_atual=Decimal(str(round(scores[-1], 2))),
                    score_projetado=Decimal(str(round(max(projected, 1.0), 2))),
                    data_points=[{'date': h['date'], 'score': h['score']} for h in recent],
                )
                alerts_created.append(alert)

    return alerts_created


def analyze_risk_growth(company):
    """
    Analisa se os riscos da empresa estão crescendo (mais riscos críticos).
    Returns: list de alertas criados.
    """
    from risk_management.models import RiskAssessment
    from .models import PredictiveAlert

    # Avaliações dos últimos 6 meses
    six_months = timezone.now() - timedelta(days=180)
    three_months = timezone.now() - timedelta(days=90)

    older = RiskAssessment.objects.filter(
        hazard__company=company,
        data_avaliacao__gte=six_months.date(),
        data_avaliacao__lt=three_months.date(),
    )
    recent = RiskAssessment.objects.filter(
        hazard__company=company,
        data_avaliacao__gte=three_months.date(),
    )

    # Contar críticos
    old_critical = older.filter(nivel_risco__in=['SUBSTANCIAL', 'INTOLERAVEL']).count()
    new_critical = recent.filter(nivel_risco__in=['SUBSTANCIAL', 'INTOLERAVEL']).count()

    alerts_created = []
    if new_critical > old_critical and new_critical > 0:
        growth = new_critical - old_critical

        existing = PredictiveAlert.objects.filter(
            company=company,
            trend_type='RISK_GROWING',
            is_acknowledged=False,
            created_at__gte=timezone.now() - timedelta(days=30)
        ).exists()

        if not existing:
            alert = PredictiveAlert.objects.create(
                company=company,
                trend_type='RISK_GROWING',
                confidence='HIGH' if growth >= 3 else 'MEDIUM',
                titulo=f'Risco crescente: +{growth} riscos críticos nos últimos 3 meses',
                descricao=(
                    f'A empresa apresentou {new_critical} riscos críticos nos últimos 3 meses, '
                    f'contra {old_critical} no trimestre anterior. '
                    f'Isso indica uma tendência de aumento de riscos ocupacionais.'
                ),
                recomendacao=(
                    f'Ação urgente requerida: revisar inventário de riscos (PGR/NR-1), '
                    f'atualizar planos de ação, e considerar treinamentos específicos. '
                    f'Avaliar necessidade de PCMSO complementar (NR-7).'
                ),
                score_atual=Decimal(str(new_critical)),
                score_projetado=Decimal(str(new_critical + growth)),
                data_points=[
                    {'period': 'trimestre_anterior', 'critical': old_critical},
                    {'period': 'trimestre_atual', 'critical': new_critical},
                ],
            )
            alerts_created.append(alert)

    return alerts_created


def analyze_dimension_trends(company):
    """
    Analisa tendência por dimensão (FDAC, Clima, Ergonomia, etc).
    Returns: list de alertas criados.
    """
    from evolution.models import DimensionEvolution
    from .models import PredictiveAlert

    # Últimas 50 evoluções
    evolutions = DimensionEvolution.objects.filter(
        company=company
    ).order_by('instrumento', 'dimensao', 'date')

    # Agrupar por dimensão
    dims = {}
    for evo in evolutions:
        key = f"{evo.instrumento}|{evo.dimensao}"
        if key not in dims:
            dims[key] = []
        dims[key].append({
            'date': evo.date.isoformat(),
            'media': float(evo.media),
            'classificacao': evo.classificacao,
        })

    alerts_created = []
    for key, history in dims.items():
        if len(history) < 2:
            continue

        recent = history[-3:] if len(history) >= 3 else history
        scores = [h['media'] for h in recent]

        # Verificar queda para "Crítico" ou tendência de queda
        is_declining = all(
            scores[i] >= scores[i + 1]
            for i in range(len(scores) - 1)
        )

        if is_declining and scores[-1] < 2.5:  # Nível Crítico
            instrumento, dimensao = key.split('|', 1)

            existing = PredictiveAlert.objects.filter(
                company=company,
                trend_type='DIMENSION_ALERT',
                dimensao=dimensao,
                is_acknowledged=False,
                created_at__gte=timezone.now() - timedelta(days=30)
            ).exists()

            if not existing:
                alert = PredictiveAlert.objects.create(
                    company=company,
                    trend_type='DIMENSION_ALERT',
                    confidence='HIGH',
                    titulo=f'Dimensão "{dimensao}" em nível CRÍTICO',
                    descricao=(
                        f'A dimensão "{dimensao}" ({instrumento}) caiu para '
                        f'{scores[-1]:.2f} (Crítico). Tendência de queda detectada '
                        f'nos últimos {len(scores)} períodos.'
                    ),
                    recomendacao=(
                        f'Ação imediata necessária na dimensão "{dimensao}". '
                        f'Revisar condições do ambiente de trabalho, aplicar medidas '
                        f'corretivas conforme PGR e realizar monitoramento intensivo.'
                    ),
                    dimensao=dimensao,
                    score_atual=Decimal(str(round(scores[-1], 2))),
                    data_points=[{'date': h['date'], 'score': h['media']} for h in recent],
                )
                alerts_created.append(alert)

    return alerts_created


def get_suggestions_for_risk(tipo_risco, nivel_risco):
    """
    Retorna sugestões automáticas baseadas no tipo e nível de risco.
    Hierarquia: INTOLERAVEL > SUBSTANCIAL > MODERADO > TOLERAVEL > TRIVIAL
    """
    from .models import NRSuggestion

    # Mapear hierarquia de severidade
    severity_order = ['TRIVIAL', 'TOLERAVEL', 'MODERADO', 'SUBSTANCIAL', 'INTOLERAVEL']
    min_index = severity_order.index(nivel_risco) if nivel_risco in severity_order else 0

    # Filtrar sugestões aplicáveis
    suggestions = NRSuggestion.objects.filter(
        tipo_risco=tipo_risco,
        is_active=True,
    )

    # Filtrar por nível mínimo de risco
    applicable_levels = severity_order[:min_index + 1]
    suggestions = suggestions.filter(nivel_risco_minimo__in=applicable_levels)

    return suggestions.order_by('prioridade')


def run_predictive_analysis():
    """
    Executa todas as análises preditivas para todas as empresas.
    Chamado pelo Celery semanalmente ou via management command.
    """
    from companies.models import Company

    companies = Company.objects.filter(status='ACTIVE')
    total_alerts = 0

    for company in companies:
        sector_alerts = analyze_sector_trends(company)
        risk_alerts = analyze_risk_growth(company)
        dimension_alerts = analyze_dimension_trends(company)

        total_alerts += len(sector_alerts) + len(risk_alerts) + len(dimension_alerts)

    return {
        'companies_analyzed': companies.count(),
        'alerts_created': total_alerts,
    }


def seed_nr_suggestions():
    """
    Popula o banco com sugestões padrão para cada tipo de risco.
    Chamar uma vez na configuração inicial do sistema.
    """
    from .models import NRSuggestion

    suggestions = [
        # Ergonômico — NR-17
        {
            'tipo_risco': 'ERGONOMICO',
            'nivel_risco_minimo': 'MODERADO',
            'norma_referencia': 'NR-17',
            'categoria': 'AMBIENTE',
            'titulo': 'Adequação do Mobiliário de Trabalho',
            'descricao': 'Ajustar altura de mesas, cadeiras com apoio lombar, monitores na linha dos olhos. Fornecer apoio para pés e descanso para pulsos conforme NR-17.',
            'fundamentacao': 'NR-17, item 17.3 — Mobiliário dos postos de trabalho. Hackman & Oldham (1976) — Job Characteristics Model.',
            'prioridade': 1,
        },
        {
            'tipo_risco': 'ERGONOMICO',
            'nivel_risco_minimo': 'SUBSTANCIAL',
            'norma_referencia': 'NR-17',
            'categoria': 'ORGANIZACIONAL',
            'titulo': 'Implementar Pausas Programadas',
            'descricao': 'Estabelecer pausas de 10 minutos a cada 50 minutos de trabalho contínuo para atividades de digitação e esforço repetitivo.',
            'fundamentacao': 'NR-17, item 17.6.3 — Pausas para descanso. Karasek (1979) — Modelo Demanda-Controle.',
            'prioridade': 2,
        },
        # Psicossocial — NR-1
        {
            'tipo_risco': 'PSICOSSOCIAL',
            'nivel_risco_minimo': 'MODERADO',
            'norma_referencia': 'NR-1',
            'categoria': 'ORGANIZACIONAL',
            'titulo': 'Programa de Gestão de Estresse Ocupacional',
            'descricao': 'Implementar programa com ações de conscientização, rodas de conversa e canal de acolhimento psicológico para funcionários.',
            'fundamentacao': 'NR-1 (GRO) — Gerenciamento de riscos psicossociais. Goulart (2025) — Modelo FDAC.',
            'prioridade': 1,
        },
        {
            'tipo_risco': 'PSICOSSOCIAL',
            'nivel_risco_minimo': 'SUBSTANCIAL',
            'norma_referencia': 'NR-1',
            'categoria': 'ACOMPANHAMENTO',
            'titulo': 'Avaliação Psicológica Individual',
            'descricao': 'Encaminhar colaboradores do setor afetado para avaliação com psicólogo do trabalho. Monitorar indicadores de burnout e ansiedade.',
            'fundamentacao': 'NR-1 — PGR item 1.5.3.3. Karasek (1979) — Modelo Demanda-Controle. Litwin & Stringer (1968) — Clima Organizacional.',
            'prioridade': 2,
        },
        # Físico — NR-1
        {
            'tipo_risco': 'FISICO',
            'nivel_risco_minimo': 'MODERADO',
            'norma_referencia': 'NR-1',
            'categoria': 'EPC',
            'titulo': 'Proteção Coletiva contra Ruído',
            'descricao': 'Instalar barreiras acústicas, enclausurar fontes de ruído e realizar manutenção preventiva de equipamentos ruidosos.',
            'fundamentacao': 'NR-1 (PGR) — Hierarquia de controles. NR-9 — Agentes físicos.',
            'prioridade': 1,
        },
        {
            'tipo_risco': 'FISICO',
            'nivel_risco_minimo': 'SUBSTANCIAL',
            'norma_referencia': 'NR-1',
            'categoria': 'EPI',
            'titulo': 'Fornecimento de EPI Específico',
            'descricao': 'Fornecer protetores auriculares tipo plug ou concha, conforme grau de exposição. Registrar entrega e treinar uso correto.',
            'fundamentacao': 'NR-6 — EPI. NR-1 item 1.5.5 — Medidas de prevenção.',
            'prioridade': 2,
        },
        # Químico — NR-7
        {
            'tipo_risco': 'QUIMICO',
            'nivel_risco_minimo': 'MODERADO',
            'norma_referencia': 'NR-7',
            'categoria': 'ACOMPANHAMENTO',
            'titulo': 'Monitoramento Biológico (PCMSO)',
            'descricao': 'Incluir exames complementares específicos no PCMSO para monitorar exposição a agentes químicos.',
            'fundamentacao': 'NR-7 — PCMSO, Quadro I. NR-1 — PGR.',
            'prioridade': 1,
        },
        # Biológico — NR-7
        {
            'tipo_risco': 'BIOLOGICO',
            'nivel_risco_minimo': 'MODERADO',
            'norma_referencia': 'NR-7',
            'categoria': 'PREVENCAO',
            'titulo': 'Protocolo de Biossegurança',
            'descricao': 'Implementar protocolo de biossegurança com higienização, descarte adequado de resíduos e vacinação ocupacional.',
            'fundamentacao': 'NR-7 — PCMSO. NR-32 — Serviços de Saúde.',
            'prioridade': 1,
        },
        # Acidente — NR-12
        {
            'tipo_risco': 'ACIDENTE',
            'nivel_risco_minimo': 'MODERADO',
            'norma_referencia': 'NR-12',
            'categoria': 'TREINAMENTO',
            'titulo': 'Treinamento de Segurança em Máquinas',
            'descricao': 'Realizar treinamento conforme NR-12 para todos os operadores. Incluir procedimentos de lock-out/tag-out.',
            'fundamentacao': 'NR-12 — Segurança no trabalho em máquinas e equipamentos.',
            'prioridade': 1,
        },
    ]

    created = 0
    for s in suggestions:
        obj, was_created = NRSuggestion.objects.get_or_create(
            tipo_risco=s['tipo_risco'],
            titulo=s['titulo'],
            defaults=s,
        )
        if was_created:
            created += 1

    return created
