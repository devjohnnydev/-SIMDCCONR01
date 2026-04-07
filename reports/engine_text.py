"""
==================================================================================
ENGINE TEXT — Motor de Texto Determinístico SIMDCCONR01
==================================================================================
Gera laudos item a item com rastreabilidade total, substituindo a análise por IA.
Hierarquia de saída: Respondente → PCMSO → Departamento → Organização.

Regras de Negócio:
  🔴 R1 — Exclusividade Bibliográfica
  🔴 R2 — Rastreabilidade Total (160/160)
  🔴 R3 — FDAC exclusivamente Goulart (2025)
  🔴 R4 — Saída obrigatória para PGR/GRO + PCMSO
  🔴 R5 — Hierarquia formal de entrega
==================================================================================
"""
from decimal import Decimal
from collections import defaultdict

from django.db.models import Avg, Count

from forms_builder.models import FormAnswer, FormAssignment, FormQuestion
from .knowledge_base import (
    classify_score,
    get_item_metadata,
    get_interpretation,
    get_recommendation,
    get_all_references,
    RISK_RULES,
    ITEM_METADATA,
)


class TextEngine:
    """
    Motor determinístico de geração de laudos SIMDCCONR01.
    Processa respostas Likert e gera saída rastreável item a item.
    """

    # ─── NÍVEL 1: Respondente (Individual) ────────────────────────────

    def generate_respondent_report(self, assignment):
        """
        Gera devolutiva completa individual (160 itens).
        Retorna dict com toda a estrutura para renderização no template.

        Args:
            assignment: FormAssignment com status COMPLETED.
        Returns:
            dict com chaves: items, summary, references, risk_level, pcmso_needed.
        """
        answers = FormAnswer.objects.filter(
            assignment=assignment
        ).select_related('question').order_by('question__order')

        items = []
        dimension_scores = defaultdict(list)
        instruments_used = set()
        pcmso_needed = False

        for answer in answers:
            order = answer.question.order
            meta = get_item_metadata(order)

            if not meta:
                continue

            # Obter valor
            value = self._get_answer_value(answer)

            # Classificar
            label, key = classify_score(value)

            # Interpretação
            interpretation = get_interpretation(
                meta['instrumento'], meta['dimensao'], key
            )

            # Recomendação individual
            recommendation = get_recommendation('respondente', key)

            # Risco
            risk_info = RISK_RULES.get(key, RISK_RULES['adequado'])

            # Agregar por dimensão
            if value is not None:
                dimension_scores[(meta['instrumento'], meta['dimensao'])].append(float(value))

            instruments_used.add(meta['instrumento'])

            # Verificar necessidade de PCMSO
            if key == 'critico' and meta['instrumento'] in ('NR-01', 'IMCO'):
                pcmso_needed = True

            items.append({
                'order': order,
                'id_item': f"{meta['instrumento']}-{order:03d}",
                'instrumento': meta['instrumento'],
                'vetor': meta['vetor'],
                'dimensao': meta['dimensao'],
                'pergunta': answer.question.text,
                'valor': value,
                'classificacao': label,
                'classificacao_key': key,
                'autor': meta['autor'],
                'ano': meta['ano'],
                'obra': meta['obra'],
                'constructo': meta['constructo'],
                'interpretacao': interpretation,
                'recomendacao': recommendation,
                'referencia_abnt': meta['referencia_abnt'],
                'risco': risk_info['risco'],
                'probabilidade': risk_info['probabilidade'],
                'impacto': risk_info['impacto'],
            })

        # Resumo por dimensão
        dimension_summary = []
        for (instrumento, dimensao), scores in sorted(dimension_scores.items()):
            avg = sum(scores) / len(scores) if scores else 0
            label, key = classify_score(avg)
            dimension_summary.append({
                'instrumento': instrumento,
                'dimensao': dimensao,
                'media': round(avg, 2),
                'classificacao': label,
                'classificacao_key': key,
                'total_items': len(scores),
            })

        # Calcular nível geral de risco
        all_scores = [s for scores in dimension_scores.values() for s in scores]
        overall_avg = sum(all_scores) / len(all_scores) if all_scores else 3.5
        overall_label, overall_key = classify_score(overall_avg)

        return {
            'items': items,
            'dimension_summary': dimension_summary,
            'overall_avg': round(overall_avg, 2),
            'overall_classification': overall_label,
            'overall_key': overall_key,
            'references': get_all_references(),
            'pcmso_needed': pcmso_needed,
            'instruments_used': sorted(instruments_used),
            'total_items': len(items),
        }

    # ─── NÍVEL 1.5: Anexo PCMSO (Individual) ─────────────────────────

    def generate_pcmso_annex(self, assignment):
        """
        Gera anexo individual obrigatório ao PCMSO.
        Baseado em Karasek (1979).

        Returns:
            dict com chaves: risk_level, recommendations, base_teorica, etc.
        """
        report = self.generate_respondent_report(assignment)

        # Filtrar dimensões de risco psicossocial específicas
        psychosocial_dims = [d for d in report['dimension_summary']
                            if d['instrumento'] in ('NR-01', 'IMCO')
                            and d['classificacao_key'] in ('critico', 'atencao')]

        critical_items = [i for i in report['items']
                         if i['classificacao_key'] == 'critico'
                         and i['instrumento'] in ('NR-01', 'IMCO')]

        # Determinar nível de risco PCMSO
        if any(d['classificacao_key'] == 'critico' for d in psychosocial_dims):
            nivel = 'Elevado'
        elif any(d['classificacao_key'] == 'atencao' for d in psychosocial_dims):
            nivel = 'Moderado'
        else:
            nivel = 'Baixo'

        # Recomendação PCMSO
        if nivel == 'Elevado':
            pcmso_key = 'critico'
        elif nivel == 'Moderado':
            pcmso_key = 'atencao'
        else:
            pcmso_key = 'adequado'

        recommendations = get_recommendation('pcmso', pcmso_key)

        # Síntese psicossocial
        if nivel == 'Elevado':
            sintese = (
                'Os resultados indicam exposição significativa a fatores de risco '
                'relacionados à organização do trabalho, com potencial impacto na '
                'saúde mental e no desempenho funcional, conforme modelo '
                'Demanda-Controle de Karasek (1979).'
            )
        elif nivel == 'Moderado':
            sintese = (
                'Os resultados indicam exposição parcial a fatores de risco '
                'psicossocial que demandam monitoramento, conforme modelo '
                'teórico adotado (Karasek, 1979).'
            )
        else:
            sintese = (
                'Os resultados indicam condições psicossociais dentro de parâmetros '
                'adequados, sem evidência de exposição significativa a fatores de '
                'risco conforme modelo teórico adotado (Karasek, 1979).'
            )

        return {
            'nivel': nivel,
            'sintese': sintese,
            'recomendacoes': recommendations,
            'base_teorica': 'Karasek, R. A. (1979). Job Demands, Job Decision Latitude, and Mental Strain.',
            'dimensoes_alerta': psychosocial_dims,
            'itens_criticos': critical_items,
            'overall': report['overall_classification'],
            'overall_avg': report['overall_avg'],
            'observacao': (
                'Documento deve ser anexado à ficha admissional e '
                'atualizado conforme evolução do colaborador.'
            ),
        }

    # ─── NÍVEL 2: Departamento ────────────────────────────────────────

    def generate_department_report(self, form_instance, sector_name):
        """
        Gera consolidação por departamento/centro de custo.
        Agrega todos os respondentes do setor.

        Returns:
            dict com consolidação IMCO, FDAC, NR-01, NR-17, NR-12 e clusters de risco.
        """
        assignments = FormAssignment.objects.filter(
            form_instance=form_instance,
            employee__setor=sector_name,
            status='COMPLETED'
        )

        if not assignments.exists():
            return {'error': 'Nenhuma resposta concluída para este departamento.'}

        # Agregar scores por dimensão
        dimension_scores = defaultdict(list)
        total_respondents = assignments.count()

        for assignment in assignments:
            answers = FormAnswer.objects.filter(
                assignment=assignment
            ).select_related('question')

            for answer in answers:
                order = answer.question.order
                meta = get_item_metadata(order)
                if not meta:
                    continue

                value = self._get_answer_value(answer)
                if value is not None:
                    dimension_scores[(meta['instrumento'], meta['dimensao'])].append(float(value))

        # Calcular médias por dimensão
        consolidation = []
        risk_clusters = []

        for (instrumento, dimensao), scores in sorted(dimension_scores.items()):
            avg = sum(scores) / len(scores) if scores else 0
            label, key = classify_score(avg)
            risk_info = RISK_RULES.get(key, RISK_RULES['adequado'])

            entry = {
                'instrumento': instrumento,
                'dimensao': dimensao,
                'media': round(avg, 2),
                'classificacao': label,
                'classificacao_key': key,
                'total_respostas': len(scores),
                'risco': risk_info['risco'],
                'probabilidade': risk_info['probabilidade'],
                'impacto': risk_info['impacto'],
            }
            consolidation.append(entry)

            if key in ('critico', 'atencao'):
                risk_clusters.append(entry)

        # Separar por instrumento
        imco_items = [c for c in consolidation if c['instrumento'] == 'IMCO']
        fdac_items = [c for c in consolidation if c['instrumento'] == 'FDAC']
        nr01_items = [c for c in consolidation if c['instrumento'] == 'NR-01']

        # Scores gerais por instrumento
        all_scores = [s for scores in dimension_scores.values() for s in scores]
        overall_avg = sum(all_scores) / len(all_scores) if all_scores else 3.5
        overall_label, overall_key = classify_score(overall_avg)

        return {
            'setor': sector_name,
            'total_respondentes': total_respondents,
            'consolidation': consolidation,
            'imco': imco_items,
            'fdac': fdac_items,
            'nr01': nr01_items,
            'risk_clusters': risk_clusters,
            'overall_avg': round(overall_avg, 2),
            'overall_classification': overall_label,
            'overall_key': overall_key,
            'references': get_all_references(),
        }

    # ─── NÍVEL 3: Organização (Laudo Pericial) ────────────────────────

    def generate_organizational_laudo(self, form_instance):
        """
        Gera laudo pericial organizacional completo.
        Inclui análise completa, matriz de risco, recomendações SESMT e
        integração com PGR/GRO, PCMSO, NR-17 e NR-12.

        Returns:
            dict com toda a estrutura do laudo pericial.
        """
        company = form_instance.company

        # Obter todos os setores com respostas
        from employees.models import Employee
        sectors = Employee.objects.filter(
            company=company,
            status='ACTIVE',
            form_assignments__form_instance=form_instance,
            form_assignments__status='COMPLETED'
        ).values_list('setor', flat=True).distinct()

        # Gerar relatório por departamento
        department_reports = []
        for sector in sectors:
            if sector:
                dept_report = self.generate_department_report(form_instance, sector)
                if 'error' not in dept_report:
                    department_reports.append(dept_report)

        # Consolidação geral
        all_dimension_scores = defaultdict(list)
        total_respondents = 0

        completed_assignments = FormAssignment.objects.filter(
            form_instance=form_instance,
            status='COMPLETED'
        )
        total_respondents = completed_assignments.count()

        for assignment in completed_assignments:
            answers = FormAnswer.objects.filter(
                assignment=assignment
            ).select_related('question')

            for answer in answers:
                order = answer.question.order
                meta = get_item_metadata(order)
                if not meta:
                    continue
                value = self._get_answer_value(answer)
                if value is not None:
                    all_dimension_scores[(meta['instrumento'], meta['dimensao'])].append(float(value))

        # Matriz de risco organizacional
        risk_matrix = []
        for (instrumento, dimensao), scores in sorted(all_dimension_scores.items()):
            avg = sum(scores) / len(scores) if scores else 0
            label, key = classify_score(avg)
            risk_info = RISK_RULES.get(key, RISK_RULES['adequado'])

            interpretation = get_interpretation(instrumento, dimensao, key)
            org_recommendation = get_recommendation('organizacao', key)

            risk_matrix.append({
                'instrumento': instrumento,
                'dimensao': dimensao,
                'media': round(avg, 2),
                'classificacao': label,
                'classificacao_key': key,
                'risco': risk_info['risco'],
                'probabilidade': risk_info['probabilidade'],
                'impacto': risk_info['impacto'],
                'acao_pgr': risk_info['acao_pgr'],
                'interpretacao': interpretation,
                'recomendacao': org_recommendation,
            })

        # Separar por instrumento para o laudo
        imco_matrix = [r for r in risk_matrix if r['instrumento'] == 'IMCO']
        fdac_matrix = [r for r in risk_matrix if r['instrumento'] == 'FDAC']
        nr01_matrix = [r for r in risk_matrix if r['instrumento'] == 'NR-01']
        nr17_items = [r for r in risk_matrix if 'Ergonomia' in r['dimensao'] or 'NR-17' in r['dimensao']]
        nr12_items = [r for r in risk_matrix if 'NR-12' in r['dimensao']]

        # Scores gerais
        all_scores = [s for scores in all_dimension_scores.values() for s in scores]
        overall_avg = sum(all_scores) / len(all_scores) if all_scores else 3.5
        overall_label, overall_key = classify_score(overall_avg)

        # SESMT - Integração PGR/GRO
        pgr_items = [r for r in risk_matrix if r['classificacao_key'] in ('critico', 'atencao')]

        sesmt = {
            'pgr_gro': {
                'items': pgr_items,
                'total_riscos': len(pgr_items),
                'riscos_criticos': len([r for r in pgr_items if r['classificacao_key'] == 'critico']),
                'riscos_atencao': len([r for r in pgr_items if r['classificacao_key'] == 'atencao']),
            },
            'nr17': {
                'items': nr17_items,
                'achado': self._nr17_achado(nr17_items),
                'acoes': self._nr17_acoes(nr17_items),
                'base_teorica': 'Hackman & Oldham (1976)',
            },
            'nr12': {
                'items': nr12_items,
                'achado': self._nr12_achado(nr12_items),
                'acoes': self._nr12_acoes(nr12_items),
                'base_normativa': 'NR-12',
            },
        }

        # Conclusão pericial
        conclusao = self._gerar_conclusao(overall_key, pgr_items)

        # Dados para gráficos
        chart_data = {
            'radar': {dim: round(sum(scores) / len(scores), 2)
                     for (inst, dim), scores in all_dimension_scores.items()
                     if inst == 'IMCO'},
            'heatmap': {},
            'likert_distribution': self._likert_distribution(form_instance),
        }

        # Heatmap por departamento
        for dept in department_reports:
            chart_data['heatmap'][dept['setor']] = {
                'score': dept['overall_avg'],
                'classificacao': dept['overall_classification'],
            }

        return {
            'company': company,
            'total_respondentes': total_respondents,
            'risk_matrix': risk_matrix,
            'imco': imco_matrix,
            'fdac': fdac_matrix,
            'nr01': nr01_matrix,
            'department_reports': department_reports,
            'sesmt': sesmt,
            'overall_avg': round(overall_avg, 2),
            'overall_classification': overall_label,
            'overall_key': overall_key,
            'conclusao': conclusao,
            'chart_data': chart_data,
            'references': get_all_references(),
        }

    # ─── HELPERS ──────────────────────────────────────────────────────

    def _get_answer_value(self, answer):
        """Extrai o valor numérico de uma resposta para classificação."""
        if answer.question.question_type in ('SCALE', 'SCALE_10', 'NUMBER'):
            return float(answer.numeric_value) if answer.numeric_value is not None else None
        elif answer.question.question_type == 'YESNO':
            # Sim = 1 (risco), Não = 5 (sem risco) — para itens de risco
            if answer.boolean_value is None:
                return None
            return 1.0 if answer.boolean_value else 5.0
        elif answer.question.question_type == 'SINGLE':
            # Para blocos L (0-3), normalizar para escala 1-5
            if answer.numeric_value is not None:
                val = float(answer.numeric_value)
                # Normalizar: 0→5, 1→3.8, 2→2.5, 3→1
                mapping = {0: 5.0, 1: 3.8, 2: 2.5, 3: 1.0}
                return mapping.get(int(val), 3.0)
            return None
        return None

    def _nr17_achado(self, items):
        """Gera achado NR-17 baseado nos itens."""
        criticos = [i for i in items if i['classificacao_key'] == 'critico']
        if criticos:
            return 'Sobrecarga cognitiva e/ou inadequação organizacional identificada.'
        atencao = [i for i in items if i['classificacao_key'] == 'atencao']
        if atencao:
            return 'Sinais de sobrecarga ergonômica que demandam atenção.'
        return 'Condições ergonômicas dentro dos parâmetros adequados.'

    def _nr17_acoes(self, items):
        """Gera ações NR-17."""
        criticos = [i for i in items if i['classificacao_key'] in ('critico', 'atencao')]
        if criticos:
            return [
                'Redesenho do trabalho',
                'Ajuste de pausas',
                'Revisão de tarefas simultâneas',
                'Avaliação ergonômica do posto de trabalho',
            ]
        return ['Manutenção das condições atuais']

    def _nr12_achado(self, items):
        """Gera achado NR-12."""
        criticos = [i for i in items if i['classificacao_key'] == 'critico']
        if criticos:
            return 'Percepção de risco e/ou falha comportamental em segurança de máquinas.'
        atencao = [i for i in items if i['classificacao_key'] == 'atencao']
        if atencao:
            return 'Percepção de risco moderada em segurança de máquinas e equipamentos.'
        return 'Dispositivos de segurança percebidos como adequados e funcionais.'

    def _nr12_acoes(self, items):
        """Gera ações NR-12."""
        criticos = [i for i in items if i['classificacao_key'] in ('critico', 'atencao')]
        if criticos:
            return [
                'Reforço de treinamento',
                'Padronização de procedimentos',
                'Supervisão operacional',
                'Verificação de dispositivos de segurança',
            ]
        return ['Manutenção dos procedimentos atuais']

    def _gerar_conclusao(self, overall_key, pgr_items):
        """Gera a conclusão pericial final."""
        base = (
            'Os resultados evidenciam, com base em análise item a item e fundamentação '
            'teórica rastreável, '
        )

        if overall_key == 'critico':
            return base + (
                'a existência de fatores organizacionais críticos que impactam diretamente '
                'o clima, a cultura e os riscos ocupacionais. '
                'A integração dos achados ao PGR/GRO e ao PCMSO é obrigatória para '
                'atendimento à NR-01, sendo recomendadas intervenções estruturais, '
                'organizacionais e de monitoramento contínuo. '
                'A manutenção do cenário identificado pode ensejar riscos trabalhistas, '
                'civis e operacionais.'
            )
        elif overall_key == 'atencao':
            return base + (
                'a existência de fatores organizacionais em nível de atenção que demandam '
                'monitoramento e ações preventivas. '
                'Recomenda-se a integração dos achados ao PGR/GRO e ao PCMSO, '
                'com planejamento de ações corretivas para as dimensões identificadas.'
            )
        elif overall_key == 'adequado':
            return base + (
                'condições organizacionais dentro de parâmetros adequados. '
                'Recomenda-se a manutenção das práticas atuais com monitoramento periódico, '
                'garantindo a integração dos dados ao PGR/GRO e PCMSO.'
            )
        else:
            return base + (
                'condições organizacionais fortes em todas as dimensões avaliadas. '
                'Recomenda-se a manutenção e disseminação das boas práticas identificadas, '
                'com registro adequado no PGR/GRO e PCMSO.'
            )

    def _likert_distribution(self, form_instance):
        """Calcula a distribuição Likert (1-5) de todas as respostas SCALE."""
        distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}

        answers = FormAnswer.objects.filter(
            assignment__form_instance=form_instance,
            question__question_type='SCALE'
        )

        for answer in answers:
            if answer.numeric_value is not None:
                val = int(answer.numeric_value)
                if 1 <= val <= 5:
                    distribution[val] += 1

        return distribution
