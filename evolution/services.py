"""
Serviço de criação de snapshots de evolução.
Chamado automaticamente ao gerar laudos organizacionais.
"""
from django.utils import timezone
from collections import defaultdict

from .models import EvolutionSnapshot, RiskScoreHistory, DimensionEvolution


def create_snapshot_from_report(form_instance, report_data, user=None):
    """
    Cria um EvolutionSnapshot a partir dos dados de um laudo organizacional.

    Args:
        form_instance: FormInstance do laudo gerado
        report_data: dict retornado por TextEngine.generate_organizational_laudo()
        user: Usuário que gerou o laudo
    """
    company = form_instance.company

    # Dimension scores
    dimension_scores = {}
    for item in report_data.get('risk_matrix', []):
        key = f"{item['instrumento']}|{item['dimensao']}"
        dimension_scores[key] = item['media']

    # Sector scores
    sector_scores = {}
    for dept in report_data.get('department_reports', []):
        sector_scores[dept['setor']] = dept['overall_avg']

    # Risk count by type
    risk_count = defaultdict(int)
    for item in report_data.get('risk_matrix', []):
        risk_count[item['classificacao_key']] += 1

    # PCMSO alertas
    pcmso_count = len([
        item for item in report_data.get('risk_matrix', [])
        if item.get('classificacao_key') == 'critico'
        and item.get('instrumento') in ('NR-01', 'IMCO')
    ])

    # Criar ou atualizar snapshot
    snapshot, created = EvolutionSnapshot.objects.update_or_create(
        company=company,
        form_instance=form_instance,
        defaults={
            'snapshot_date': timezone.now().date(),
            'overall_score': report_data.get('overall_avg', 3.5),
            'overall_classification': report_data.get('overall_classification', 'Adequado'),
            'dimension_scores': dimension_scores,
            'sector_scores': sector_scores,
            'risk_count_by_type': dict(risk_count),
            'total_respondentes': report_data.get('total_respondentes', 0),
            'total_itens_analisados': len(report_data.get('risk_matrix', [])),
            'pcmso_alertas': pcmso_count,
            'created_by': user,
        }
    )

    # Criar registros de evolução por dimensão
    for item in report_data.get('risk_matrix', []):
        DimensionEvolution.objects.update_or_create(
            company=company,
            snapshot=snapshot,
            instrumento=item['instrumento'],
            dimensao=item['dimensao'],
            defaults={
                'media': item['media'],
                'classificacao': item['classificacao'],
                'total_respostas': item.get('total_respostas', 0),
                'date': timezone.now().date(),
            }
        )

    # Calcular Risk Score (0-100)
    # Converte de escala Likert (1-5, onde 1=pior) para score de risco (0-100, onde 100=pior)
    overall_avg = float(report_data.get('overall_avg', 3.5))
    # Inverter: 1 → 100, 5 → 0
    risk_score = int(max(0, min(100, (5 - overall_avg) / 4 * 100)))

    # Scores por tipo de risco
    type_scores = {'fisico': 0, 'quimico': 0, 'biologico': 0, 'ergonomico': 0, 'psicossocial': 0}
    type_counts_calc = {'fisico': 0, 'quimico': 0, 'biologico': 0, 'ergonomico': 0, 'psicossocial': 0}

    # Mapear instrumentos para tipos de risco
    instrument_to_type = {
        'NR-01': 'psicossocial',
        'IMCO': 'psicossocial',
        'FDAC': 'psicossocial',
        'NR-17': 'ergonomico',
        'NR-12': 'fisico',
    }

    for item in report_data.get('risk_matrix', []):
        rtype = instrument_to_type.get(item['instrumento'], 'psicossocial')
        media = float(item.get('media', 3.5))
        score = int(max(0, min(100, (5 - media) / 4 * 100)))
        type_scores[rtype] += score
        type_counts_calc[rtype] += 1

    # Médias por tipo
    for rtype in type_scores:
        if type_counts_calc[rtype] > 0:
            type_scores[rtype] = int(type_scores[rtype] / type_counts_calc[rtype])

    RiskScoreHistory.objects.create(
        company=company,
        score=risk_score,
        score_fisico=type_scores['fisico'],
        score_quimico=type_scores['quimico'],
        score_biologico=type_scores['biologico'],
        score_ergonomico=type_scores['ergonomico'],
        score_psicossocial=type_scores['psicossocial'],
    )

    return snapshot
