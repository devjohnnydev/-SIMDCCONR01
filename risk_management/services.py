"""
==================================================================================
SERVICES — Geração Automática de Perigos e Comparação de Pesquisas
==================================================================================
Motor inteligente que analisa resultados de pesquisas SIMDCCONR01 e:
1. Gera HazardRegistry automaticamente para dimensões críticas/atenção
2. Compara pesquisas anteriores vs. atuais para detectar evolução
3. Atualiza status de perigos existentes baseado na evolução
==================================================================================
"""
import logging
from decimal import Decimal
from collections import defaultdict

from django.utils import timezone

from .models import HazardRegistry, RiskAssessment
from reports.engine_text import TextEngine
from reports.knowledge_base import classify_score, get_interpretation, RISK_RULES

logger = logging.getLogger(__name__)


# ─── Mapeamento Instrumento → Tipo de Risco ─────────────────────────────
INSTRUMENT_TO_RISK_TYPE = {
    'IMCO': 'PSICOSSOCIAL',
    'FDAC': 'PSICOSSOCIAL',
    'NR-01': 'PSICOSSOCIAL',
    'NR-17': 'ERGONOMICO',
    'NR-12': 'ACIDENTE',
}

INSTRUMENT_TO_NORM = {
    'IMCO': 'NR-1',
    'FDAC': 'NR-1',
    'NR-01': 'NR-1',
    'NR-17': 'NR-17',
    'NR-12': 'NR-12',
}


def auto_generate_hazards(form_instance, user=None):
    """
    Analisa resultados da pesquisa e gera HazardRegistry automaticamente.
    
    Cada dimensão com classificação 'critico' ou 'atencao' gera um perigo
    com status PENDING_REVIEW para aprovação do admin.
    
    Args:
        form_instance: FormInstance com status CLOSED ou com respostas suficientes.
        user: User que disparou a ação (admin).
    
    Returns:
        dict com contagem de perigos gerados e detalhes.
    """
    engine = TextEngine()
    company = form_instance.company
    
    # Gerar laudo organizacional para obter scores por dimensão
    laudo_data = engine.generate_organizational_laudo(form_instance)
    risk_matrix = laudo_data.get('risk_matrix', [])
    
    generated = []
    skipped = []
    
    for item in risk_matrix:
        key = item.get('classificacao_key', 'adequado')
        
        # Apenas gerar perigos para dimensões críticas ou atenção
        if key not in ('critico', 'atencao'):
            continue
        
        instrumento = item.get('instrumento', '')
        dimensao = item.get('dimensao', '')
        media = item.get('media', 0)
        
        # Verificar se já existe perigo ativo para esta dimensão/instrumento/empresa/pesquisa
        existing = HazardRegistry.objects.filter(
            company=company,
            form_instance=form_instance,
            source_dimension=dimensao,
            source_instrument=instrumento,
        ).exists()
        
        if existing:
            skipped.append(f"{instrumento}/{dimensao}")
            continue
        
        # Determinar tipo de risco e norma
        tipo_risco = INSTRUMENT_TO_RISK_TYPE.get(instrumento, 'PSICOSSOCIAL')
        norma = INSTRUMENT_TO_NORM.get(instrumento, 'NR-1')
        
        # Gerar descrição profissional do perigo
        interpretacao = item.get('interpretacao', '')
        recomendacao = item.get('recomendacao', '')
        
        descricao = (
            f"[{dimensao}] {interpretacao}\n\n"
            f"Classificação: {item.get('classificacao', '')} (média: {media}/5.0)\n"
            f"Risco: {item.get('risco', '')} — Probabilidade: {item.get('probabilidade', '')} | "
            f"Impacto: {item.get('impacto', '')}"
        )
        
        fonte = f"Pesquisa SIMDCCONR01 — {form_instance.title} (ID: {form_instance.pk})"
        
        # Obter setores dos respondentes
        from forms_builder.models import FormAssignment
        setores = FormAssignment.objects.filter(
            form_instance=form_instance,
            status='COMPLETED'
        ).values_list('employee__setor', flat=True).distinct()
        setor_text = ', '.join([s for s in setores if s]) or 'Todos os setores'
        
        hazard = HazardRegistry.objects.create(
            company=company,
            setor=setor_text,
            funcao='Todos os cargos avaliados',
            atividade=f'Diagnóstico {instrumento} — Dimensão: {dimensao}',
            descricao_perigo=descricao,
            fonte_geradora=fonte,
            tipo_risco=tipo_risco,
            norma_referencia=norma,
            status='PENDING_REVIEW',
            auto_generated=True,
            source_dimension=dimensao,
            source_instrument=instrumento,
            source_score=Decimal(str(round(media, 2))),
            form_instance=form_instance,
            identified_by=user,
        )
        
        # Criar avaliação de risco automática
        risk_info = RISK_RULES.get(key, RISK_RULES['adequado'])
        prob = 4 if key == 'critico' else 3
        sev = 4 if key == 'critico' else 3
        
        RiskAssessment.objects.create(
            hazard=hazard,
            probabilidade=prob,
            severidade=sev,
            justificativa=(
                f"Avaliação automática baseada no diagnóstico SIMDCCONR01. "
                f"Dimensão '{dimensao}' classificada como '{item.get('classificacao', '')}' "
                f"com média {media}/5.0. Ação PGR: {risk_info.get('acao_pgr', '')}"
            ),
            avaliado_por=user,
        )
        
        generated.append({
            'instrumento': instrumento,
            'dimensao': dimensao,
            'media': media,
            'classificacao': item.get('classificacao', ''),
            'hazard_pk': hazard.pk,
        })
    
    logger.info(
        f"Auto-generate hazards para {company.nome_fantasia}: "
        f"{len(generated)} gerados, {len(skipped)} pulados"
    )
    
    return {
        'generated': generated,
        'skipped': skipped,
        'total_generated': len(generated),
        'total_skipped': len(skipped),
    }


def compare_surveys(current_form, previous_form):
    """
    Compara duas aplicações do mesmo template para detectar evolução.
    
    Args:
        current_form: FormInstance mais recente (CLOSED).
        previous_form: FormInstance anterior (CLOSED).
    
    Returns:
        dict com evolução por dimensão:
        {
            'dimensions': [
                {
                    'instrumento': 'IMCO',
                    'dimensao': 'Reconhecimento',
                    'anterior': 2.3,
                    'atual': 3.8,
                    'variacao': 1.5,
                    'percentual': 65.2,
                    'status': 'MELHORA_SIGNIFICATIVA',
                    'status_label': 'Melhora Significativa',
                    'interpretacao': '...',
                },
            ],
            'overall': {...},
            'hazards_updated': [...],
        }
    """
    engine = TextEngine()
    
    current_data = engine.generate_organizational_laudo(current_form)
    previous_data = engine.generate_organizational_laudo(previous_form)
    
    # Mapear scores por dimensão para cada pesquisa
    current_scores = {}
    for item in current_data.get('risk_matrix', []):
        key = (item['instrumento'], item['dimensao'])
        current_scores[key] = item
    
    previous_scores = {}
    for item in previous_data.get('risk_matrix', []):
        key = (item['instrumento'], item['dimensao'])
        previous_scores[key] = item
    
    # Comparar todas as dimensões
    all_dims = set(current_scores.keys()) | set(previous_scores.keys())
    
    dimensions = []
    for (instrumento, dimensao) in sorted(all_dims):
        curr = current_scores.get((instrumento, dimensao))
        prev = previous_scores.get((instrumento, dimensao))
        
        if not curr or not prev:
            continue
        
        anterior = prev['media']
        atual = curr['media']
        variacao = round(atual - anterior, 2)
        percentual = round((variacao / anterior * 100), 1) if anterior > 0 else 0
        
        # Classificar evolução
        status, status_label = _classify_evolution(anterior, atual, variacao)
        
        # Interpretação contextual
        interpretacao = _generate_evolution_text(
            instrumento, dimensao, anterior, atual, status
        )
        
        dimensions.append({
            'instrumento': instrumento,
            'dimensao': dimensao,
            'vetor': curr.get('vetor', prev.get('vetor', '')),
            'anterior': anterior,
            'atual': atual,
            'variacao': variacao,
            'percentual': percentual,
            'status': status,
            'status_label': status_label,
            'classificacao_anterior': prev.get('classificacao', ''),
            'classificacao_atual': curr.get('classificacao', ''),
            'interpretacao': interpretacao,
        })
    
    # Overall comparison
    overall = {
        'anterior': previous_data.get('overall_avg', 0),
        'atual': current_data.get('overall_avg', 0),
        'variacao': round(
            current_data.get('overall_avg', 0) - previous_data.get('overall_avg', 0), 2
        ),
        'classificacao_anterior': previous_data.get('overall_classification', ''),
        'classificacao_atual': current_data.get('overall_classification', ''),
    }
    overall_status, overall_label = _classify_evolution(
        overall['anterior'], overall['atual'], overall['variacao']
    )
    overall['status'] = overall_status
    overall['status_label'] = overall_label
    
    return {
        'dimensions': dimensions,
        'overall': overall,
        'current_form': current_form,
        'previous_form': previous_form,
        'total_dimensions': len(dimensions),
        'melhorias': len([d for d in dimensions if 'MELHORA' in d['status']]),
        'pioras': len([d for d in dimensions if 'PIORA' in d['status']]),
        'sanados': len([d for d in dimensions if d['status'] == 'SANADO']),
        'estaveis': len([d for d in dimensions if d['status'] == 'ESTAVEL']),
    }


def update_hazards_from_comparison(company, comparison_result, form_instance, user=None):
    """
    Atualiza o status dos perigos existentes com base na comparação de pesquisas.
    
    - Dimensões que melhoraram de 'critico/atencao' para 'adequado/forte' → MITIGATED
    - Dimensões completamente sanadas → ELIMINATED
    """
    updated = []
    
    for dim in comparison_result.get('dimensions', []):
        status = dim['status']
        instrumento = dim['instrumento']
        dimensao = dim['dimensao']
        
        # Buscar perigos ativos vinculados a esta dimensão
        hazards = HazardRegistry.objects.filter(
            company=company,
            source_dimension=dimensao,
            source_instrument=instrumento,
            status='ACTIVE',
        )
        
        if not hazards.exists():
            continue
        
        if status == 'SANADO':
            # Dimensão totalmente resolvida
            for h in hazards:
                h.status = 'ELIMINATED'
                h.save(update_fields=['status', 'updated_at'])
                updated.append({
                    'hazard_pk': h.pk,
                    'dimensao': dimensao,
                    'novo_status': 'ELIMINATED',
                })
        elif status in ('MELHORA_SIGNIFICATIVA',):
            # Melhora significativa — mitigar
            cls_atual = dim.get('classificacao_atual', '')
            if cls_atual in ('Adequado', 'Forte'):
                for h in hazards:
                    h.status = 'MITIGATED'
                    h.save(update_fields=['status', 'updated_at'])
                    updated.append({
                        'hazard_pk': h.pk,
                        'dimensao': dimensao,
                        'novo_status': 'MITIGATED',
                    })
    
    return updated


def _classify_evolution(anterior, atual, variacao):
    """Classifica a evolução entre duas pontuações."""
    _, key_anterior = classify_score(anterior)
    _, key_atual = classify_score(atual)
    
    # Sanado: era crítico/atenção, agora é adequado/forte
    if key_anterior in ('critico', 'atencao') and key_atual in ('adequado', 'forte'):
        return 'SANADO', 'Problema Sanado'
    
    # Melhora significativa: variação > 0.8
    if variacao >= 0.8:
        return 'MELHORA_SIGNIFICATIVA', 'Melhora Significativa'
    
    # Melhora leve: variação entre 0.3 e 0.8
    if 0.3 <= variacao < 0.8:
        return 'MELHORA_LEVE', 'Melhora Leve'
    
    # Estável: variação entre -0.3 e 0.3
    if -0.3 < variacao < 0.3:
        return 'ESTAVEL', 'Estável'
    
    # Piora leve: variação entre -0.8 e -0.3
    if -0.8 < variacao <= -0.3:
        return 'PIORA_LEVE', 'Piora Leve'
    
    # Piora significativa: variação < -0.8
    return 'PIORA_SIGNIFICATIVA', 'Piora Significativa'


def _generate_evolution_text(instrumento, dimensao, anterior, atual, status):
    """Gera texto interpretativo da evolução."""
    _, key_anterior = classify_score(anterior)
    _, key_atual = classify_score(atual)
    
    templates = {
        'SANADO': (
            f'A dimensão "{dimensao}" ({instrumento}) apresentou melhora completa, '
            f'passando de {anterior:.2f} para {atual:.2f}. O risco identificado '
            f'anteriormente foi sanado com êxito pelas ações implementadas.'
        ),
        'MELHORA_SIGNIFICATIVA': (
            f'A dimensão "{dimensao}" ({instrumento}) apresentou melhora significativa, '
            f'passando de {anterior:.2f} para {atual:.2f}. As intervenções implementadas '
            f'demonstram eficácia e devem ser mantidas e consolidadas.'
        ),
        'MELHORA_LEVE': (
            f'A dimensão "{dimensao}" ({instrumento}) apresentou melhora leve, '
            f'passando de {anterior:.2f} para {atual:.2f}. Recomenda-se a intensificação '
            f'das ações para atingir níveis adequados.'
        ),
        'ESTAVEL': (
            f'A dimensão "{dimensao}" ({instrumento}) manteve-se estável, '
            f'permanecendo em {atual:.2f}. Recomenda-se revisão da estratégia de '
            f'intervenção caso o nível esteja abaixo do adequado.'
        ),
        'PIORA_LEVE': (
            f'A dimensão "{dimensao}" ({instrumento}) apresentou piora leve, '
            f'passando de {anterior:.2f} para {atual:.2f}. Atenção requerida para '
            f'reverter a tendência negativa.'
        ),
        'PIORA_SIGNIFICATIVA': (
            f'A dimensão "{dimensao}" ({instrumento}) apresentou piora significativa, '
            f'passando de {anterior:.2f} para {atual:.2f}. Intervenção urgente recomendada. '
            f'Incluir no PGR/GRO com prioridade máxima.'
        ),
    }
    
    return templates.get(status, f'Dimensão "{dimensao}": {anterior:.2f} → {atual:.2f}')
