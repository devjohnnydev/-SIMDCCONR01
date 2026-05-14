"""
==================================================================================
UTILS PDF (REPORTLAB) — Industrial Standard PDF Generation for SIMDCCONR01
==================================================================================
Este módulo substitui o FPDF2 para garantir total compatibilidade com visualizadores
de PDF modernos (Chrome/Edge) e eliminar erros de segurança de carregamento.
==================================================================================
v2.1 — Fix: spacing, logo, signature rendering
==================================================================================
"""
import os
import math
import logging
import io
import xml.sax.saxutils as saxutils
from django.utils import timezone
from datetime import timedelta
from django.conf import settings

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.pdfgen import canvas
from reportlab.platypus import Flowable

def format_ai_data(data):
    if not data: return ""
    if isinstance(data, str): return data
    if isinstance(data, list):
        return "\n".join([f"• {item}" for item in data])
    if isinstance(data, dict):
        lines = []
        for k, v in data.items():
            k_fmt = str(k).replace('_', ' ').title()
            lines.append(f"<b>{k_fmt}:</b> {v}")
        return "\n".join(lines)
    return str(data)

logger = logging.getLogger(__name__)

# Paleta de Cores Premium
COL_BLUE = colors.HexColor("#2563eb")
COL_DARK = colors.HexColor("#0f172a")
COL_SLATE_50 = colors.HexColor("#f8fafc")
COL_SLATE_100 = colors.HexColor("#f1f5f9")
COL_SLATE_500 = colors.HexColor("#64748b")
COL_DANGER = colors.HexColor("#fee2e2")
COL_WARNING = colors.HexColor("#fef3c7")
COL_SUCCESS = colors.HexColor("#dcfce7")
COL_GREEN = colors.HexColor("#16a34a")
COL_FORTE = colors.HexColor("#dbeafe")


def _color_for_key(key):
    """Retorna a cor de fundo para uma classificação."""
    return {'critico': COL_DANGER, 'atencao': COL_WARNING,
            'adequado': COL_SUCCESS, 'forte': COL_FORTE}.get(key, colors.transparent)


def _build_vetor_dimension_table(styles, items, title='Matriz de Risco por Vetor e Dimensão'):
    """
    Constrói uma tabela profissional com VETOR × DIMENSÃO × MÉDIA × CLASSIFICAÇÃO × RISCO.
    Usado em todos os 3 tipos de relatório.
    """
    from reportlab.platypus import Table, TableStyle, Paragraph
    
    header = ['VETOR', 'DIMENSÃO', 'INSTR.', 'MÉDIA', 'CLASS.', 'RISCO (PGR)']
    col_widths = [30*mm, 38*mm, 14*mm, 14*mm, 22*mm, 60*mm]
    
    data = [[Paragraph(f"<font size=7><b>{h}</b></font>", styles['Normal']) for h in header]]
    
    for item in items:
        vetor = item.get('vetor', item.get('dimensao', ''))
        data.append([
            Paragraph(f"<font size=7>{saxutils.escape(str(vetor))}</font>", styles['Normal']),
            Paragraph(f"<font size=7>{saxutils.escape(str(item.get('dimensao', '')))}</font>", styles['Normal']),
            Paragraph(f"<font size=7 color='#2563eb'>{str(item.get('instrumento', ''))}</font>", styles['Normal']),
            Paragraph(f"<font size=8><b>{item.get('media', '-')}</b></font>", styles['Normal']),
            Paragraph(f"<font size=7><b>{saxutils.escape(str(item.get('classificacao', '-')))}</b></font>", styles['Normal']),
            Paragraph(f"<font size=6 color='#64748b'>{saxutils.escape(str(item.get('acao_pgr', item.get('risco', '-'))))}</font>", styles['Normal']),
        ])
    
    tbl = Table(data, colWidths=col_widths, repeatRows=1)
    style_cmds = [
        ('BACKGROUND', (0, 0), (-1, 0), COL_DARK),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('INNERGRID', (0, 0), (-1, -1), 0.25, COL_SLATE_100),
        ('BOX', (0, 0), (-1, -1), 0.5, COL_SLATE_100),
        ('FONTSIZE', (0, 0), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
    ]
    for row_idx in range(1, len(data)):
        it = items[row_idx - 1]
        clr = _color_for_key(it.get('classificacao_key', ''))
        style_cmds.append(('BACKGROUND', (4, row_idx), (4, row_idx), clr))
    tbl.setStyle(TableStyle(style_cmds))
    return tbl


class RadarChartFlowable(Flowable):
    """Flowable que desenha o radar chart. Retorna height=0 se nao houver dados."""
    def __init__(self, respondent_report_rl, dimension_summary, width=120*mm, height=80*mm):
        Flowable.__init__(self)
        self.dimension_summary = dimension_summary
        self.rr = respondent_report_rl
        # Verifica se existem dados IMCO com >= 3 dimensoes
        imco_data = {d['dimensao']: d['media'] for d in dimension_summary if d.get('instrumento') == 'IMCO'}
        if len(imco_data) >= 3:
            self.width = width
            self.height = height
            self._has_data = True
        else:
            self.width = 0
            self.height = 0
            self._has_data = False

    def draw(self):
        if self._has_data:
            self.rr._draw_radar(self.canv, self.width / 2.0, self.height / 2.0, self.dimension_summary)


class RespondentReportRL:
    def __init__(self, buffer, company=None, diagnostic=None):
        self.buffer = buffer
        self.company = company
        self.diagnostic = diagnostic
        self.generated_at = timezone.now()
        self.styles = getSampleStyleSheet()
        self._setup_styles()
        self._logo_image_data = None
        self._preload_logo()

    def _preload_logo(self):
        """Carrega o logo do sistema SIMDCCONR01 (static/img/logo.png)."""
        try:
            # Tenta carregar o logo padrão do sistema em static
            logo_path = os.path.join(settings.BASE_DIR, 'static', 'img', 'logo.png')
            if os.path.exists(logo_path):
                with open(logo_path, 'rb') as f:
                    self._logo_image_data = f.read()
                logger.info("Logo do sistema carregado com sucesso (Respondent)")
            else:
                logger.warning(f"Logo do sistema não encontrado: {logo_path}")
        except Exception as e:
            logger.error(f"Erro ao carregar logo do sistema: {e}")

    def _setup_styles(self):
        # Custom Title Style
        self.styles.add(ParagraphStyle(
            name='ReportTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            textColor=COL_DARK,
            alignment=2, # Right
            spaceAfter=2
        ))

        self.styles.add(ParagraphStyle(
            name='ReportSubtitle',
            fontSize=8,
            textColor=COL_BLUE,
            alignment=2,
            textTransform='uppercase',
            fontName='Helvetica-Bold'
        ))

        self.styles.add(ParagraphStyle(
            name='SectionHeading',
            fontSize=11,
            textColor=colors.whitesmoke,
            background=COL_DARK,
            backColor=COL_DARK,
            borderPadding=5,
            fontName='Helvetica-Bold',
            spaceBefore=10,
            spaceAfter=10
        ))

        self.styles.add(ParagraphStyle(
            name='AnalysisBox',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=COL_DARK,
            leftIndent=10,
            rightIndent=10,
            firstLineIndent=0,
            alignment=4, # Justify
            leading=14,
            borderWidth=0,
            borderColor=COL_BLUE,
            borderPadding=(5, 10, 5, 10),
            backColor=COL_SLATE_100
        ))

    def _draw_header(self, canvas, doc):
        """Desenha header e footer em TODAS as paginas."""
        canvas.saveState()

        # ── LOGO (superior esquerdo) ──
        logo_drawn = False
        if self._logo_image_data:
            try:
                from reportlab.lib.utils import ImageReader
                img_reader = ImageReader(io.BytesIO(self._logo_image_data))
                canvas.drawImage(img_reader, 15*mm, 270*mm, height=12*mm, width=12*mm, preserveAspectRatio=True, mask='auto')
                logo_drawn = True
            except Exception as e:
                logger.warning(f"Erro ao desenhar logo no header: {e}")

        # SEMPRE mostrar o nome SIMDCCONR01
        canvas.setFont('Helvetica-Bold', 18)
        canvas.setFillColor(COL_BLUE)
        text_x = 30*mm if logo_drawn else 15*mm
        canvas.drawString(text_x, 272*mm, "SIMDCCONR01")

        # ── TITULO (superior direito) ──
        canvas.setFont('Helvetica-Bold', 14)
        canvas.setFillColor(COL_DARK)
        canvas.drawRightString(195*mm, 275*mm, "Parecer Técnico Pericial")

        canvas.setFont('Helvetica-Bold', 7)
        canvas.setFillColor(COL_BLUE)
        canvas.drawRightString(195*mm, 271*mm, "DOCUMENTO OFICIAL · RASTREABILIDADE TOTAL")

        # ── LINHA SEPARADORA ──
        canvas.setStrokeColor(COL_BLUE)
        canvas.setLineWidth(0.8)
        canvas.line(15*mm, 268*mm, 195*mm, 268*mm)

        # ── FOOTER ──
        canvas.setFont('Helvetica-Oblique', 8)
        canvas.setFillColor(COL_SLATE_500)
        page_num = canvas.getPageNumber()
        canvas.drawCentredString(105*mm, 10*mm, f"Página {page_num} — Parecer Técnico SIMDCCONR01")

        canvas.restoreState()

    def _draw_radar(self, canvas, x, y, dimension_summary):
        """Desenha o gráfico radar diretamente no canvas."""
        data = {dim['dimensao']: dim['media'] for dim in dimension_summary if dim.get('instrumento') == 'IMCO'}
        if not data: return

        labels = list(data.keys())
        values = list(data.values())
        n = len(labels)
        if n < 3: return

        max_r = 30*mm
        max_val = 5.0

        # Grid Circles
        canvas.setStrokeColor(colors.lightgrey)
        canvas.setLineWidth(0.1)
        for level in range(1, 6):
            r = max_r * (level / max_val)
            canvas.circle(x, y, r, stroke=1, fill=0)

        # Axes & Labels
        angles = [(i * 360 / n) - 90 for i in range(n)]
        canvas.setFont('Helvetica-Bold', 7)
        canvas.setFillColor(COL_DARK)

        for i, angle_deg in enumerate(angles):
            rad = math.radians(angle_deg)
            # Line
            canvas.setStrokeColor(COL_SLATE_500)
            canvas.setLineWidth(0.5)
            canvas.line(x, y, x + max_r*math.cos(rad), y + max_r*math.sin(rad))
            # Label
            dist = max_r + (15*mm if i % 2 == 0 else 5*mm)
            lx = x + dist*math.cos(rad)
            ly = y + dist*math.sin(rad)
            
            words = labels[i].split(' ')
            if len(labels[i]) > 12 and len(words) >= 2:
                lines = [words[0], " ".join(words[1:])]
            else:
                lines = [labels[i]]
            lines = [l[:16] + ".." if len(l) > 16 else l for l in lines]
            
            canvas.setFont('Helvetica-Bold', 5.5)
            line_height = 6
            start_y = ly + (len(lines) - 1) * (line_height / 2) - 2
            
            for idx_l, line_txt in enumerate(lines):
                draw_y = start_y - (idx_l * line_height)
                if math.cos(rad) > 0.1:
                    canvas.drawString(lx, draw_y, line_txt.upper())
                elif math.cos(rad) < -0.1:
                    canvas.drawRightString(lx, draw_y, line_txt.upper())
                else:
                    canvas.drawCentredString(lx, draw_y, line_txt.upper())

        # Data Polygon
        points = []
        for i, val in enumerate(values):
            r = max_r * (min(val, max_val) / max_val)
            rad = math.radians(angles[i])
            points.append((x + r*math.cos(rad), y + r*math.sin(rad)))

        p = canvas.beginPath()
        p.moveTo(points[0][0], points[0][1])
        for i in range(1, len(points)):
            p.lineTo(points[i][0], points[i][1])
        p.close()

        canvas.setFillColor(COL_BLUE, alpha=0.25)
        canvas.setStrokeColor(COL_BLUE)
        canvas.setLineWidth(1.5)
        canvas.drawPath(p, stroke=1, fill=1)

        # Dots
        canvas.setFillColor(COL_BLUE)
        for pt in points:
            canvas.circle(pt[0], pt[1], 1.2*mm, stroke=0, fill=1)

    def build(self, report_data, sections, **kwargs):
        doc = SimpleDocTemplate(
            self.buffer,
            pagesize=A4,
            rightMargin=15*mm,
            leftMargin=15*mm,
            topMargin=35*mm,
            bottomMargin=20*mm
        )

        story = []

        # ═══════════════════════════════════════════════
        # 1. TITULO
        # ═══════════════════════════════════════════════
        story.append(Spacer(1, 3*mm))
        story.append(Paragraph("SÍNTESE DE RESULTADOS", self.styles['ReportTitle']))
        story.append(Paragraph("ANÁLISE DE SAÚDE MENTAL E CLIMA", self.styles['ReportSubtitle']))
        story.append(Spacer(1, 6*mm))

        # ═══════════════════════════════════════════════
        # 2. INFO CARD (Tabela Estilizada)
        # ═══════════════════════════════════════════════
        emp = self.diagnostic.assignment.employee
        info_data = [
            [Paragraph(f"<font color='#64748b' size=7>FUNCIONÁRIO</font><br/><b>{saxutils.escape(emp.nome.upper())}</b>", self.styles['Normal']),
             Paragraph(f"<font color='#64748b' size=7>CPF</font><br/><b>{saxutils.escape(emp.cpf or 'Não informado')}</b>", self.styles['Normal'])],
            [Paragraph(f"<font color='#64748b' size=7>EMPRESA</font><br/><b>{saxutils.escape(self.company.nome_fantasia.upper()) if self.company else '-'}</b>", self.styles['Normal']),
             Paragraph(f"<font color='#64748b' size=7>DATA DA AVALIAÇÃO</font><br/><b>{(self.generated_at - timedelta(hours=3)).strftime('%d/%m/%Y %H:%M')}</b>", self.styles['Normal'])],
            [Paragraph(f"<font color='#64748b' size=7>SETOR E CARGO</font><br/><b>{saxutils.escape(emp.setor)} — {saxutils.escape(emp.cargo)}</b>", self.styles['Normal']), ""]
        ]
        info_table = Table(info_data, colWidths=[110*mm, 70*mm])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), COL_SLATE_50),
            ('BORDER', (0, 0), (-1, -1), 0.5, COL_SLATE_100),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.white),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('SPAN', (0, 2), (1, 2)),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(info_table)
        story.append(Spacer(1, 4*mm))

        # ═══════════════════════════════════════════════
        # 3. RADAR CHART (altura dinamica — 0 se sem dados)
        # ═══════════════════════════════════════════════
        radar = RadarChartFlowable(self, report_data.get('dimension_summary', []), width=180*mm, height=75*mm)
        if radar._has_data:
            story.append(radar)
            story.append(Spacer(1, 4*mm))

        # ═══════════════════════════════════════════════
        # 3.1 TABELA VETOR × DIMENSÃO (Resumo Individual)
        # ═══════════════════════════════════════════════
        dim_summary = report_data.get('dimension_summary', [])
        if dim_summary:
            story.append(Paragraph("Síntese por Vetor e Dimensão", self.styles['Heading2']))
            # Converter dimension_summary para o formato esperado pela tabela
            items_for_table = []
            for dim in dim_summary:
                from reports.knowledge_base import RISK_RULES
                key = dim.get('classificacao_key', 'adequado')
                risk_info = RISK_RULES.get(key, RISK_RULES['adequado'])
                items_for_table.append({
                    'vetor': dim.get('vetor', ''),
                    'dimensao': dim.get('dimensao', ''),
                    'instrumento': dim.get('instrumento', ''),
                    'media': dim.get('media', 0),
                    'classificacao': dim.get('classificacao', ''),
                    'classificacao_key': key,
                    'acao_pgr': risk_info.get('acao_pgr', ''),
                })
            story.append(_build_vetor_dimension_table(self.styles, items_for_table))
            story.append(Spacer(1, 6*mm))

        # ═══════════════════════════════════════════════
        # 4. RELATÓRIO ESTRUTURADO (sem PageBreak!)
        # ═══════════════════════════════════════════════
        story.append(Paragraph("Relatório Estruturado", self.styles['Heading2']))

        for section in sections:
            # Header da seção
            section_label = saxutils.escape(f"{section['meta']['number']}. {section['meta']['label']}")
            story.append(Paragraph(section_label, self.styles['SectionHeading']))

            # Texto Qualitativo
            if section.get('text'):
                formatted_text = format_ai_data(section['text'])
                safe_text = saxutils.escape(formatted_text)
                safe_text = safe_text.replace('\n', '<br/>').replace('&lt;b&gt;', '<b>').replace('&lt;/b&gt;', '</b>')
                story.append(Paragraph(safe_text, self.styles['AnalysisBox']))
                story.append(Spacer(1, 6))

            # Tabela de Itens
            item_data = [['ID', 'ITEM / PERGUNTA', 'REF.', 'VAL.', 'STATUS']]
            col_widths = [15*mm, 85*mm, 35*mm, 15*mm, 30*mm]

            for item in section.get('items', []):
                ref = f"{item.get('constructo', '')}\n({item.get('ano', '')})"
                status = item.get('classificacao', '-')

                safe_pergunta = saxutils.escape(item.get('pergunta', '-')).replace('\n', '<br/>')
                safe_ref = saxutils.escape(ref).replace('\n', '<br/>')

                item_data.append([
                    Paragraph(f"<font color='#64748b'>{saxutils.escape(item.get('id_item', '-'))}</font>", self.styles['Normal']),
                    Paragraph(safe_pergunta, self.styles['Normal']),
                    Paragraph(f"<font size=7 color='#64748b'>{safe_ref}</font>", self.styles['Normal']),
                    Paragraph(str(item.get('valor') or "-"), self.styles['Normal']),
                    Paragraph(f"<b>{saxutils.escape(status)}</b>", self.styles['Normal'])
                ])

            items_table = Table(item_data, colWidths=col_widths, repeatRows=1)
            items_table_style = [
                ('BACKGROUND', (0, 0), (-1, 0), COL_DARK),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('INNERGRID', (0, 0), (-1, -1), 0.25, COL_SLATE_100),
                ('BOX', (0, 0), (-1, -1), 0.5, COL_SLATE_100),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
            ]

            # Colorir celula de status por linha
            for row_idx in range(1, len(item_data)):
                it = section['items'][row_idx - 1]
                clr = colors.transparent
                if it.get('classificacao_key') == 'critico': clr = COL_DANGER
                elif it.get('classificacao_key') == 'atencao': clr = COL_WARNING
                elif it.get('classificacao_key') == 'adequado': clr = COL_SUCCESS
                items_table_style.append(('BACKGROUND', (4, row_idx), (4, row_idx), clr))

            items_table.setStyle(TableStyle(items_table_style))
            story.append(items_table)
            story.append(Spacer(1, 10))

        # Recuperar kwargs
        pcmso_data = kwargs.get('pcmso_data')
        dim_analysis = kwargs.get('dim_analysis')
        pgr_items = kwargs.get('pgr_items')

        # ═══════════════════════════════════════════════
        # 5. ANÁLISE POR DIMENSÃO (Teórica)
        # ═══════════════════════════════════════════════
        if dim_analysis:
            story.append(Spacer(1, 5*mm))
            story.append(Paragraph("5. Análise por Dimensão — Fundamentação Teórica", self.styles['Heading2']))
            for dim in dim_analysis:
                story.append(Paragraph(f"<b>{saxutils.escape(str(dim.get('dimensao', '')))} ({saxutils.escape(str(dim.get('vetor', '')))}) — {str(dim.get('instrumento', ''))}</b>", self.styles['Heading4']))
                if dim.get('interpretacao'):
                    story.append(Paragraph(saxutils.escape(str(dim['interpretacao'])), self.styles['Normal']))
                story.append(Paragraph(f"<font color='#64748b' size='8'>Média: {dim.get('media', '-')} | Risco: {dim.get('risco', '-')} | PGR: {dim.get('acao_pgr', '-')}</font>", self.styles['Normal']))
                if dim.get('recomendacao'):
                    story.append(Paragraph(f"<b>Recomendação:</b> {saxutils.escape(str(dim['recomendacao']))}", self.styles['Normal']))
                story.append(Spacer(1, 4*mm))

        # ═══════════════════════════════════════════════
        # 6. ANEXO PCMSO
        # ═══════════════════════════════════════════════
        if pcmso_data:
            story.append(Spacer(1, 5*mm))
            story.append(Paragraph("6. Anexo PCMSO — Saúde Ocupacional Individual", self.styles['Heading2']))
            story.append(Paragraph(f"<b>Risco Psicossocial:</b> {str(pcmso_data.get('nivel', ''))}", self.styles['Normal']))
            story.append(Paragraph(f"<b>Classificação Geral:</b> {str(pcmso_data.get('overall', ''))} ({str(pcmso_data.get('overall_avg', ''))})", self.styles['Normal']))
            story.append(Spacer(1, 2*mm))
            story.append(Paragraph("<b>Síntese Psicossocial:</b>", self.styles['Normal']))
            story.append(Paragraph(saxutils.escape(str(pcmso_data.get('sintese', ''))), self.styles['Normal']))
            story.append(Spacer(1, 2*mm))
            story.append(Paragraph("<b>Recomendações Clínicas:</b>", self.styles['Normal']))
            story.append(Paragraph(saxutils.escape(str(pcmso_data.get('recomendacoes', ''))), self.styles['Normal']))
            story.append(Spacer(1, 5*mm))

        # ═══════════════════════════════════════════════
        # 7. INTEGRAÇÃO PGR/GRO
        # ═══════════════════════════════════════════════
        if pgr_items:
            story.append(Spacer(1, 5*mm))
            story.append(Paragraph("7. Integração PGR/GRO — Inventário de Riscos", self.styles['Heading2']))
            story.append(Paragraph("<font size='8' color='#64748b'>Dimensões classificadas como Crítico ou Atenção com integração obrigatória ao PGR (NR-01).</font>", self.styles['Normal']))
            story.append(Spacer(1, 3*mm))
            pgr_table_data = [['DIMENSÃO', 'VETOR', 'MÉDIA', 'PROB', 'IMP', 'AÇÃO PGR']]
            for item in pgr_items:
                pgr_table_data.append([
                    Paragraph(f"<font size='7'>{saxutils.escape(str(item.get('dimensao', '')))}</font>", self.styles['Normal']),
                    Paragraph(f"<font size='7'>{saxutils.escape(str(item.get('vetor', '')))}</font>", self.styles['Normal']),
                    str(item.get('media', '-')),
                    str(item.get('probabilidade', '-')),
                    str(item.get('impacto', '-')),
                    Paragraph(f"<font size='7'>{saxutils.escape(str(item.get('acao_pgr', '')))}</font>", self.styles['Normal'])
                ])
            pgr_table = Table(pgr_table_data, colWidths=[35*mm, 25*mm, 15*mm, 15*mm, 15*mm, 75*mm])
            pgr_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), COL_DARK),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('INNERGRID', (0, 0), (-1, -1), 0.25, COL_SLATE_100),
                ('BOX', (0, 0), (-1, -1), 0.5, COL_SLATE_100),
                ('FONTSIZE', (0, 0), (-1, -1), 7),
            ]))
            story.append(pgr_table)
            story.append(Spacer(1, 5*mm))

        # ═══════════════════════════════════════════════
        # 8. NOTA METODOLÓGICA E CONCLUSÃO
        # ═══════════════════════════════════════════════
        story.append(Spacer(1, 5*mm))
        story.append(Paragraph("8. Nota Metodológica", self.styles['Heading2']))
        story.append(Paragraph("<b>Instrumento:</b> SIMDCCONR01 — 160 itens distribuídos em IMCO (88), FDAC (12) e NR-01/SESMT (46). Validação: Coda et al. (2009).", self.styles['Normal']))
        story.append(Paragraph("<b>Escala:</b> Likert 1-5. Crítico (1.0-2.4), Atenção (2.5-3.4), Adequado (3.5-4.2), Forte (4.3-5.0).", self.styles['Normal']))
        story.append(Paragraph("<b>Normativa:</b> NR-01 (Portaria 1.419/2024), NR-17, NR-12, LGPD.", self.styles['Normal']))
        story.append(Spacer(1, 4*mm))
        
        story.append(Paragraph("9. Conclusão Pericial", self.styles['Heading2']))
        overall = report_data.get('overall_key', 'adequado')
        if overall == 'critico':
            conc_txt = "Os resultados evidenciam a existência de fatores organizacionais críticos que impactam diretamente o clima e os riscos ocupacionais. A integração ao PGR/GRO é obrigatória."
        elif overall == 'atencao':
            conc_txt = "Os resultados evidenciam a existência de fatores em nível de atenção que demandam monitoramento e ações preventivas integradas ao PGR/GRO."
        elif overall == 'adequado':
            conc_txt = "Os resultados evidenciam condições organizacionais dentro de parâmetros adequados. Recomenda-se a manutenção das práticas atuais."
        else:
            conc_txt = "Os resultados evidenciam condições organizacionais fortes em todas as dimensões avaliadas."
            
        story.append(Paragraph(conc_txt, self.styles['AnalysisBox']))
        story.append(Spacer(1, 2*mm))
        story.append(Paragraph("<font size='7' color='#64748b'>Ressalva legal: Este documento constitui parecer técnico pericial elaborado com base em instrumento validado. O sigilo é garantido conforme LGPD.</font>", self.styles['Normal']))

        # ═══════════════════════════════════════════════
        # 5. ASSINATURA PROFISSIONAL
        # ═══════════════════════════════════════════════
        story.append(Spacer(1, 10*mm))

        # Estilos dedicados para assinatura
        s_line = ParagraphStyle('s_line', parent=self.styles['Normal'], fontSize=10, alignment=1, textColor=COL_SLATE_500)
        s_name = ParagraphStyle('s_name', parent=self.styles['Normal'], fontSize=13, fontName='Helvetica-Bold', alignment=1, textColor=COL_DARK, spaceBefore=2, spaceAfter=1)
        s_spec = ParagraphStyle('s_spec', parent=self.styles['Normal'], fontSize=9, fontName='Helvetica', alignment=1, textColor=COL_BLUE, spaceAfter=1)
        s_date = ParagraphStyle('s_date', parent=self.styles['Normal'], fontSize=8, fontName='Helvetica-Oblique', alignment=1, textColor=COL_SLATE_500)
        s_badge = ParagraphStyle('s_badge', parent=self.styles['Normal'], fontSize=7, fontName='Helvetica-Bold', alignment=1, textColor=COL_GREEN, spaceBefore=4)
        s_pending = ParagraphStyle('s_pending', parent=self.styles['Normal'], fontSize=10, fontName='Helvetica-Oblique', alignment=1, textColor=COL_SLATE_500)

        if self.diagnostic.is_signed:
            signer = getattr(self.diagnostic, 'signer_profile', None)
            user_signer = getattr(self.diagnostic, 'signed_by', None)
            sig_img = None

            # 1. Tentar base64 do SignerProfile
            if signer and getattr(signer, 'signature_base64', None):
                try:
                    import base64
                    b64_str = signer.signature_base64
                    if "," in b64_str:
                        b64_str = b64_str.split(",")[1]
                    img_data = base64.b64decode(b64_str)
                    sig_img = Image(io.BytesIO(img_data), width=50*mm, height=15*mm)
                except Exception as e:
                    logger.error(f"Erro base64 signature: {e}")

            # 2. Tentar imagem do SignerProfile
            elif signer and getattr(signer, 'signature_image', None):
                try:
                    with signer.signature_image.open('rb') as f:
                        sig_img = Image(io.BytesIO(f.read()), width=50*mm, height=15*mm)
                except Exception as e:
                    logger.error(f"Erro image signature (signer): {e}")

            # 3. Tentar imagem do User
            elif user_signer and getattr(user_signer, 'signature_image', None):
                try:
                    with user_signer.signature_image.open('rb') as f:
                        sig_img = Image(io.BytesIO(f.read()), width=50*mm, height=15*mm)
                except Exception as e:
                    logger.error(f"Erro image signature (user): {e}")

            # Nome e Especialidade (escapados para XML)
            if signer:
                name = saxutils.escape(signer.nome_completo)
                reg = signer.registro_profissional or ''
                espec = ''
                try:
                    espec = signer.get_especialidade_display()
                except Exception:
                    espec = str(signer.especialidade)
                spec = saxutils.escape(f"{espec} — {reg}" if reg else espec)
            elif user_signer:
                full = user_signer.get_full_name() or ''
                name = saxutils.escape(full if full.strip() else user_signer.email)
                crp = getattr(user_signer, 'professional_crp', '') or ''
                spec_text = f"Profissional Especializado — {crp}" if crp else "Profissional Especializado"
                spec = saxutils.escape(spec_text)
            else:
                name = "Assinado Digitalmente"
                spec = ""

            ts = ""
            if self.diagnostic.signature_timestamp:
                ts = (self.diagnostic.signature_timestamp - timedelta(hours=3)).strftime('%d/%m/%Y %H:%M')

            # Montar linhas da tabela de assinatura com objetos Paragraph
            sig_rows = []
            if sig_img:
                sig_rows.append([sig_img])
            sig_rows.append([Paragraph("____________________________________", s_line)])
            sig_rows.append([Paragraph(name, s_name)])
            if spec:
                sig_rows.append([Paragraph(spec, s_spec)])
            sig_rows.append([Paragraph(f"Autenticado em {ts}", s_date)])
            sig_rows.append([Paragraph("\u2713 DOCUMENTO ASSINADO ELETRONICAMENTE", s_badge)])
        else:
            # Pendente
            sig_rows = [
                [Paragraph("____________________________________", s_line)],
                [Paragraph("Aguardando Assinatura Eletr\u00f4nica", s_pending)],
            ]

        # Tabela interna com borda e fundo
        sig_table = Table(sig_rows, colWidths=[120*mm])
        sig_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 15),
            ('RIGHTPADDING', (0, 0), (-1, -1), 15),
            ('BOX', (0, 0), (-1, -1), 1.0, COL_BLUE),
            ('BACKGROUND', (0, 0), (-1, -1), COL_SLATE_50),
            ('LINEBELOW', (0, 0), (-1, 0), 0.5, COL_SLATE_100),
        ]))

        # Wrapper para centralizar
        wrapper = Table([[sig_table]], colWidths=[180*mm])
        wrapper.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ]))
        story.append(wrapper)

        # ═══════════════════════════════════════════════
        # 6. BIBLIOGRAFIA E RASTREABILIDADE
        # ═══════════════════════════════════════════════
        story.append(Spacer(1, 10*mm))
        story.append(Paragraph("5. Bibliografia e Rastreabilidade (Modelo FDAC)", self.styles['Heading3']))
        ref_p = []
        for r in report_data.get('references', [])[:5]:
            safe_r = saxutils.escape(r)
            ref_p.append(f"\u2022 {safe_r}")
        if ref_p:
            story.append(Paragraph("<br/>".join(ref_p), self.styles['Normal']))

        story.append(Spacer(1, 10))
        vc = saxutils.escape(str(self.diagnostic.validation_code))
        story.append(Paragraph(f"<font size='7' color='#64748b'>C\u00f3digo de Autentica\u00e7\u00e3o: {vc}</font>", self.styles['Normal']))

        # ═══════════════════════════════════════════════
        # METADATA E BUILD FINAL
        # ═══════════════════════════════════════════════
        doc.title = f"Laudo {emp.nome}"
        doc.author = "SIMDCCONR01"

        try:
            doc.build(story,
                onFirstPage=self._draw_header,
                onLaterPages=self._draw_header
            )
        except Exception as e:
            logger.error(f"Erro no build do ReportLab: {e}")
            raise e


class DepartmentReportRL:
    """Gera laudo profissional para departamentos/setores consolidado."""
    def __init__(self, buffer, company=None, diagnostic=None):
        self.buffer = buffer
        self.company = company
        self.diagnostic = diagnostic
        self.generated_at = diagnostic.generated_at if diagnostic else timezone.now()
        self.styles = getSampleStyleSheet()
        self._setup_styles()
        self._logo_image_data = None
        self._preload_logo()

    def _preload_logo(self):
        """Carrega o logo do sistema SIMDCCONR01 (static/img/logo.png)."""
        try:
            # Tenta carregar o logo padrão do sistema em static
            logo_path = os.path.join(settings.BASE_DIR, 'static', 'img', 'logo.png')
            if os.path.exists(logo_path):
                with open(logo_path, 'rb') as f:
                    self._logo_image_data = f.read()
                logger.info("Logo do sistema carregado com sucesso")
            else:
                logger.warning(f"Logo do sistema não encontrado em: {logo_path}")
        except Exception as e:
            logger.error(f"Erro ao carregar logo do sistema: {e}")

    def _setup_styles(self):
        # Reaproveita estilos do RespondentReportRL ou cria novos se necessário
        self.styles.add(ParagraphStyle(
            name='DeptTitle',
            parent=self.styles['Heading1'],
            fontSize=16,
            textColor=COL_DARK,
            alignment=2,
            spaceAfter=2
        ))
        self.styles.add(ParagraphStyle(
            name='DeptSubtitle',
            fontSize=9,
            textColor=COL_BLUE,
            alignment=2,
            textTransform='uppercase',
            fontName='Helvetica-Bold'
        ))

    def _draw_header(self, canvas, doc):
        canvas.saveState()
        # Branding superior esquerdo
        logo_drawn = False
        if self._logo_image_data:
            try:
                from reportlab.lib.utils import ImageReader
                img_reader = ImageReader(io.BytesIO(self._logo_image_data))
                canvas.drawImage(img_reader, 15*mm, 270*mm, height=12*mm, width=12*mm, preserveAspectRatio=True, mask='auto')
                logo_drawn = True
            except: pass
        
        # Desenhar "SIMDCCONR01" ao lado do logo (ou sozinho se não houver logo)
        text_x = 30*mm if logo_drawn else 15*mm
        canvas.setFont('Helvetica-Bold', 18)
        canvas.setFillColor(COL_BLUE)
        canvas.drawString(text_x, 272*mm, "SIMDCCONR01")

        # Título superior direito
        canvas.setFont('Helvetica-Bold', 14)
        canvas.setFillColor(COL_DARK)
        canvas.drawRightString(195*mm, 275*mm, "Relatório Socioemocional Setorial")
        
        canvas.setFont('Helvetica-Bold', 7)
        canvas.setFillColor(COL_BLUE)
        canvas.drawRightString(195*mm, 271*mm, "CONSOLIDADO DE GRUPO · ANALISE ESTATÍSTICA")

        canvas.setStrokeColor(COL_BLUE)
        canvas.setLineWidth(0.8)
        canvas.line(15*mm, 268*mm, 195*mm, 268*mm)

        # Footer
        canvas.setFont('Helvetica-Oblique', 8)
        canvas.setFillColor(COL_SLATE_500)
        canvas.drawCentredString(105*mm, 10*mm, f"Página {canvas.getPageNumber()} — Consolidado SIMDCCONR01")
        canvas.restoreState()

    def _draw_radar(self, canvas, x, y, dimension_summary):
        """Desenha o gráfico radar diretamente no canvas."""
        data = {dim['dimensao']: dim['media'] for dim in dimension_summary if dim.get('instrumento') == 'IMCO'}
        if not data: return

        labels = list(data.keys())
        values = list(data.values())
        n = len(labels)
        if n < 3: return

        max_r = 30*mm
        max_val = 5.0

        # Grid Circles
        canvas.setStrokeColor(colors.lightgrey)
        canvas.setLineWidth(0.1)
        for level in range(1, 6):
            r = max_r * (level / max_val)
            canvas.circle(x, y, r, stroke=1, fill=0)

        # Axes & Labels
        angles = [(i * 360 / n) - 90 for i in range(n)]
        canvas.setFont('Helvetica-Bold', 7)
        canvas.setFillColor(COL_DARK)

        for i, angle_deg in enumerate(angles):
            rad = math.radians(angle_deg)
            # Line
            canvas.setStrokeColor(COL_SLATE_500)
            canvas.setLineWidth(0.5)
            canvas.line(x, y, x + max_r*math.cos(rad), y + max_r*math.sin(rad))
            # Label
            dist = max_r + (15*mm if i % 2 == 0 else 5*mm)
            lx = x + dist*math.cos(rad)
            ly = y + dist*math.sin(rad)
            
            words = labels[i].split(' ')
            if len(labels[i]) > 12 and len(words) >= 2:
                lines = [words[0], " ".join(words[1:])]
            else:
                lines = [labels[i]]
            lines = [l[:16] + ".." if len(l) > 16 else l for l in lines]
            
            canvas.setFont('Helvetica-Bold', 5.5)
            line_height = 6
            start_y = ly + (len(lines) - 1) * (line_height / 2) - 2
            
            for idx_l, line_txt in enumerate(lines):
                draw_y = start_y - (idx_l * line_height)
                if math.cos(rad) > 0.1:
                    canvas.drawString(lx, draw_y, line_txt.upper())
                elif math.cos(rad) < -0.1:
                    canvas.drawRightString(lx, draw_y, line_txt.upper())
                else:
                    canvas.drawCentredString(lx, draw_y, line_txt.upper())

        # Data Polygon
        points = []
        for i, val in enumerate(values):
            r = max_r * (min(val, max_val) / max_val)
            rad = math.radians(angles[i])
            points.append((x + r*math.cos(rad), y + r*math.sin(rad)))

        p = canvas.beginPath()
        p.moveTo(points[0][0], points[0][1])
        for i in range(1, len(points)):
            p.lineTo(points[i][0], points[i][1])
        p.close()

        canvas.setFillColor(COL_BLUE, alpha=0.25)
        canvas.setStrokeColor(COL_BLUE)
        canvas.setLineWidth(1.5)
        canvas.drawPath(p, stroke=1, fill=1)

        # Dots
        canvas.setFillColor(COL_BLUE)
        for pt in points:
            canvas.circle(pt[0], pt[1], 1.2*mm, stroke=0, fill=1)

    def build(self, data, engine_data=None, **kwargs):
        if engine_data is None:
            engine_data = {}
            
        doc = SimpleDocTemplate(
            self.buffer,
            pagesize=A4,
            rightMargin=15*mm,
            leftMargin=15*mm,
            topMargin=35*mm,
            bottomMargin=20*mm
        )
        story = []
        
        # 1. Título
        story.append(Spacer(1, 5*mm))
        story.append(Paragraph(f"DIAGNÓSTICO: {self.diagnostic.setor.upper()}", self.styles['DeptTitle']))
        story.append(Paragraph(f"EMPRESA: {self.company.nome_fantasia.upper()}", self.styles['DeptSubtitle']))
        story.append(Spacer(1, 8*mm))

        # 2. Métricas de Destaque
        idx = data.get('indice_bem_estar', 0)
        overall_avg = engine_data.get('overall_avg', '—')
        total_resp = engine_data.get('total_respondentes', '—')
        
        metrics_data = [
            [
             Paragraph(f"<font color='#64748b' size=8>RESPONDENTES</font><br/><b>{total_resp}</b>", self.styles['Normal']),
             Paragraph(f"<font color='#64748b' size=8>MÉDIA GERAL</font><br/><b>{overall_avg} / 5.0</b>", self.styles['Normal']),
             Paragraph(f"<font color='white' size=8>BEM-ESTAR DO GRUPO</font><br/><font color='white' size=14><b>{idx}%</b></font>", self.styles['Normal'])
            ]
        ]
        metrics_table = Table(metrics_data, colWidths=[60*mm, 60*mm, 60*mm])
        metrics_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (1, 0), COL_SLATE_50),
            ('BACKGROUND', (2, 0), (2, 0), COL_BLUE),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.white),
            ('BOX', (0, 0), (-1, -1), 0.5, COL_SLATE_100),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(metrics_table)
        story.append(Spacer(1, 8*mm))

        # Radar Chart
        radar_data = engine_data.get('consolidation', [])
        radar = RadarChartFlowable(self, radar_data, width=180*mm, height=75*mm)
        if radar._has_data:
            story.append(radar)
            story.append(Spacer(1, 6*mm))

        # 3. Sumário do Clima Geral
        story.append(Paragraph("1. Síntese do Clima Setorial", self.styles['Heading2']))
        story.append(Paragraph(saxutils.escape(data.get('clima_geral', '')), self.styles['Normal']))
        story.append(Spacer(1, 8*mm))

        # Matriz de Risco por Vetor × Dimensão
        consolidation = engine_data.get('consolidation', [])
        if consolidation:
            story.append(Paragraph("2. Matriz de Risco por Vetor e Dimensão", self.styles['Heading2']))
            story.append(_build_vetor_dimension_table(self.styles, consolidation))
            story.append(Spacer(1, 8*mm))


        # 4. Pontos Fortes e Alertas
        story.append(Paragraph("3. Análise Detalhada", self.styles['Heading2']))
        
        # Pontos Fortes
        story.append(Paragraph("<b>Pontos Fortes Identificados:</b>", self.styles['Normal']))
        for p in data.get('pontos_fortes', []):
            story.append(Paragraph(f"<font color='green'>\u2713</font> {saxutils.escape(p)}", self.styles['Normal']))
        story.append(Spacer(1, 4*mm))

        # Áreas de Alerta
        story.append(Paragraph("<b>Áreas de Alerta / Riscos:</b>", self.styles['Normal']))
        for a in data.get('areas_alerta', []):
            story.append(Paragraph(f"<font color='red'>!</font> {saxutils.escape(a)}", self.styles['Normal']))
        story.append(Spacer(1, 8*mm))

        # 5. Sugestões de Gestão
        story.append(Paragraph("4. Recomendações Estratégicas para o Gestor", self.styles['Heading2']))
        for i, s in enumerate(data.get('sugestoes_gestao', []), 1):
            story.append(Paragraph(f"<b>{i}.</b> {saxutils.escape(s)}", self.styles['Normal']))
            story.append(Spacer(1, 3*mm))

        # Recuperar kwargs adicionais
        dim_analysis = kwargs.get('dim_analysis')
        pgr_items = kwargs.get('pgr_items')
        nr17_data = kwargs.get('nr17_data')
        nr12_data = kwargs.get('nr12_data')
        conclusao = kwargs.get('conclusao')

        # ═══════════════════════════════════════════════
        # 4.1 ANÁLISE POR DIMENSÃO
        # ═══════════════════════════════════════════════
        if dim_analysis:
            story.append(Spacer(1, 5*mm))
            story.append(Paragraph("Análise por Dimensão — Fundamentação Teórica", self.styles['Heading2']))
            for dim in dim_analysis:
                story.append(Paragraph(f"<b>{saxutils.escape(str(dim.get('dimensao', '')))} ({saxutils.escape(str(dim.get('vetor', '')))}) — {str(dim.get('instrumento', ''))}</b>", self.styles['Heading4']))
                if dim.get('interpretacao'):
                    story.append(Paragraph(saxutils.escape(str(dim['interpretacao'])), self.styles['Normal']))
                story.append(Paragraph(f"<font color='#64748b' size='8'>Média: {dim.get('media', '-')} | Risco: {dim.get('risco', '-')} | PGR: {dim.get('acao_pgr', '-')}</font>", self.styles['Normal']))
                if dim.get('recomendacao'):
                    story.append(Paragraph(f"<b>Recomendação:</b> {saxutils.escape(str(dim['recomendacao']))}", self.styles['Normal']))
                story.append(Spacer(1, 4*mm))

        # ═══════════════════════════════════════════════
        # 4.2 INVENTÁRIO PGR/GRO
        # ═══════════════════════════════════════════════
        if pgr_items:
            story.append(Spacer(1, 5*mm))
            story.append(Paragraph("Inventário de Riscos — PGR/GRO (NR-01)", self.styles['Heading2']))
            story.append(Paragraph("<font size='8' color='#64748b'>Dimensões classificadas como Crítico ou Atenção com integração obrigatória ao PGR (NR-01).</font>", self.styles['Normal']))
            story.append(Spacer(1, 3*mm))
            pgr_table_data = [['DIMENSÃO', 'VETOR', 'MÉDIA', 'PROB', 'IMP', 'AÇÃO PGR']]
            for item in pgr_items:
                pgr_table_data.append([
                    Paragraph(f"<font size='7'>{saxutils.escape(str(item.get('dimensao', '')))}</font>", self.styles['Normal']),
                    Paragraph(f"<font size='7'>{saxutils.escape(str(item.get('vetor', '')))}</font>", self.styles['Normal']),
                    str(item.get('media', '-')),
                    str(item.get('probabilidade', '-')),
                    str(item.get('impacto', '-')),
                    Paragraph(f"<font size='7'>{saxutils.escape(str(item.get('acao_pgr', '')))}</font>", self.styles['Normal'])
                ])
            pgr_table = Table(pgr_table_data, colWidths=[35*mm, 25*mm, 15*mm, 15*mm, 15*mm, 75*mm])
            pgr_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), COL_DARK),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('INNERGRID', (0, 0), (-1, -1), 0.25, COL_SLATE_100),
                ('BOX', (0, 0), (-1, -1), 0.5, COL_SLATE_100),
                ('FONTSIZE', (0, 0), (-1, -1), 7),
            ]))
            story.append(pgr_table)
            story.append(Spacer(1, 5*mm))

        # ═══════════════════════════════════════════════
        # 4.3 NR-17 e NR-12
        # ═══════════════════════════════════════════════
        if nr17_data and nr17_data.get('items'):
            story.append(Spacer(1, 5*mm))
            story.append(Paragraph("Achados Ergonômicos — NR-17", self.styles['Heading2']))
            story.append(Paragraph(f"<b>Achado:</b> {saxutils.escape(str(nr17_data.get('achado', '')))}", self.styles['Normal']))
            story.append(Paragraph(f"<b>Base Teórica:</b> {saxutils.escape(str(nr17_data.get('base_teorica', '')))}", self.styles['Normal']))
            for acao in nr17_data.get('acoes', []):
                story.append(Paragraph(f"\u2022 {saxutils.escape(str(acao))}", self.styles['Normal']))
            story.append(Spacer(1, 4*mm))

        if nr12_data and nr12_data.get('items'):
            story.append(Spacer(1, 5*mm))
            story.append(Paragraph("Segurança em Máquinas — NR-12", self.styles['Heading2']))
            story.append(Paragraph(f"<b>Achado:</b> {saxutils.escape(str(nr12_data.get('achado', '')))}", self.styles['Normal']))
            story.append(Paragraph(f"<b>Base Normativa:</b> {saxutils.escape(str(nr12_data.get('base_normativa', '')))}", self.styles['Normal']))
            for acao in nr12_data.get('acoes', []):
                story.append(Paragraph(f"\u2022 {saxutils.escape(str(acao))}", self.styles['Normal']))
            story.append(Spacer(1, 4*mm))

        # ═══════════════════════════════════════════════
        # NOTA METODOLÓGICA E CONCLUSÃO
        # ═══════════════════════════════════════════════
        story.append(Spacer(1, 5*mm))
        story.append(Paragraph("Nota Metodológica", self.styles['Heading2']))
        story.append(Paragraph("<b>Instrumento:</b> SIMDCCONR01 — 160 itens. Validação: Coda et al. (2009).", self.styles['Normal']))
        story.append(Paragraph("<b>Escala:</b> Likert 1-5. Crítico (1.0-2.4), Atenção (2.5-3.4), Adequado (3.5-4.2), Forte (4.3-5.0).", self.styles['Normal']))
        story.append(Paragraph("<b>Normativa:</b> NR-01 (Portaria 1.419/2024), NR-17, NR-12, LGPD.", self.styles['Normal']))
        story.append(Spacer(1, 4*mm))
        
        story.append(Paragraph("Conclusão Pericial", self.styles['Heading2']))
        story.append(Paragraph(saxutils.escape(str(conclusao or "Análise concluída conforme parâmetros do SIMDCCONR01.")), self.styles['Normal']))
        story.append(Spacer(1, 2*mm))
        story.append(Paragraph("<font size='7' color='#64748b'>Ressalva legal: Este documento constitui parecer técnico pericial elaborado com base em instrumento validado. O sigilo é garantido conforme LGPD.</font>", self.styles['Normal']))

        # 6. Referencias
        references = engine_data.get('references', [])
        if references:
            story.append(Spacer(1, 8*mm))
            story.append(Paragraph("5. Bibliografia e Rastreabilidade", self.styles['Heading3']))
            ref_p = []
            for r in references[:5]:
                safe_r = saxutils.escape(r)
                ref_p.append(f"\u2022 {safe_r}")
            if ref_p:
                story.append(Paragraph("<br/>".join(ref_p), self.styles['Normal']))

        # Autenticação
        story.append(Spacer(1, 15*mm))
        story.append(Paragraph("________________________________________________", self.styles['Normal']))
        story.append(Paragraph("<font size=8 color='#64748b'>Documento gerado eletronicamente via Motor de Análise SIMDCCONR01</font>", self.styles['Normal']))

        doc.build(story, onFirstPage=self._draw_header, onLaterPages=self._draw_header)


class OrganizationalReportRL:
    """Gera o Laudo Pericial Organizacional completo."""
    def __init__(self, buffer, company=None):
        self.buffer = buffer
        self.company = company
        self.generated_at = timezone.now()
        self.styles = getSampleStyleSheet()
        self._setup_styles()
        self._logo_image_data = None
        self._preload_logo()

    def _preload_logo(self):
        try:
            logo_path = os.path.join(settings.BASE_DIR, 'static', 'img', 'logo.png')
            if os.path.exists(logo_path):
                with open(logo_path, 'rb') as f:
                    self._logo_image_data = f.read()
        except Exception:
            pass

    def _setup_styles(self):
        self.styles.add(ParagraphStyle(
            name='OrgTitle',
            parent=self.styles['Heading1'],
            fontSize=16,
            textColor=COL_DARK,
            alignment=2,
            spaceAfter=2
        ))
        self.styles.add(ParagraphStyle(
            name='OrgSubtitle',
            fontSize=9,
            textColor=COL_BLUE,
            alignment=2,
            textTransform='uppercase',
            fontName='Helvetica-Bold'
        ))

    def _draw_header(self, canvas, doc):
        canvas.saveState()
        logo_drawn = False
        if self._logo_image_data:
            try:
                from reportlab.lib.utils import ImageReader
                img_reader = ImageReader(io.BytesIO(self._logo_image_data))
                canvas.drawImage(img_reader, 15*mm, 270*mm, height=12*mm, width=12*mm, preserveAspectRatio=True, mask='auto')
                logo_drawn = True
            except: pass
        
        text_x = 30*mm if logo_drawn else 15*mm
        canvas.setFont('Helvetica-Bold', 18)
        canvas.setFillColor(COL_BLUE)
        canvas.drawString(text_x, 272*mm, "SIMDCCONR01")

        canvas.setFont('Helvetica-Bold', 14)
        canvas.setFillColor(COL_DARK)
        canvas.drawRightString(195*mm, 275*mm, "Laudo Pericial Organizacional")
        
        canvas.setFont('Helvetica-Bold', 7)
        canvas.setFillColor(COL_BLUE)
        canvas.drawRightString(195*mm, 271*mm, "DOCUMENTO TÉCNICO · USO PERICIAL")

        canvas.setStrokeColor(COL_BLUE)
        canvas.setLineWidth(0.8)
        canvas.line(15*mm, 268*mm, 195*mm, 268*mm)

        canvas.setFont('Helvetica-Oblique', 8)
        canvas.setFillColor(COL_SLATE_500)
        canvas.drawCentredString(105*mm, 10*mm, f"Página {canvas.getPageNumber()} — Laudo Pericial Organizacional SIMDCCONR01")
        canvas.restoreState()

    def _draw_radar(self, canvas, x, y, radar_dict):
        if not radar_dict: return
        labels = list(radar_dict.keys())
        values = list(radar_dict.values())
        n = len(labels)
        if n < 3: return

        max_r = 30*mm
        max_val = 5.0

        canvas.setStrokeColor(colors.lightgrey)
        canvas.setLineWidth(0.1)
        for level in range(1, 6):
            r = max_r * (level / max_val)
            canvas.circle(x, y, r, stroke=1, fill=0)

        angles = [(i * 360 / n) - 90 for i in range(n)]
        canvas.setFont('Helvetica-Bold', 7)
        canvas.setFillColor(COL_DARK)

        for i, angle_deg in enumerate(angles):
            rad = math.radians(angle_deg)
            canvas.setStrokeColor(COL_SLATE_500)
            canvas.setLineWidth(0.5)
            canvas.line(x, y, x + max_r*math.cos(rad), y + max_r*math.sin(rad))
            dist = max_r + (15*mm if i % 2 == 0 else 5*mm)
            lx = x + dist*math.cos(rad)
            ly = y + dist*math.sin(rad)
            
            words = labels[i].split(' ')
            if len(labels[i]) > 12 and len(words) >= 2:
                lines = [words[0], " ".join(words[1:])]
            else:
                lines = [labels[i]]
            lines = [l[:16] + ".." if len(l) > 16 else l for l in lines]
            
            canvas.setFont('Helvetica-Bold', 5.5)
            line_height = 6
            start_y = ly + (len(lines) - 1) * (line_height / 2) - 2
            
            for idx_l, line_txt in enumerate(lines):
                draw_y = start_y - (idx_l * line_height)
                if math.cos(rad) > 0.1:
                    canvas.drawString(lx, draw_y, line_txt.upper())
                elif math.cos(rad) < -0.1:
                    canvas.drawRightString(lx, draw_y, line_txt.upper())
                else:
                    canvas.drawCentredString(lx, draw_y, line_txt.upper())

        points = []
        for i, val in enumerate(values):
            r = max_r * (min(val, max_val) / max_val)
            rad = math.radians(angles[i])
            points.append((x + r*math.cos(rad), y + r*math.sin(rad)))

        p = canvas.beginPath()
        p.moveTo(points[0][0], points[0][1])
        for i in range(1, len(points)):
            p.lineTo(points[i][0], points[i][1])
        p.close()

        canvas.setFillColor(COL_BLUE, alpha=0.25)
        canvas.setStrokeColor(COL_BLUE)
        canvas.setLineWidth(1.5)
        canvas.drawPath(p, stroke=1, fill=1)

        canvas.setFillColor(COL_BLUE)
        for pt in points:
            canvas.circle(pt[0], pt[1], 1.2*mm, stroke=0, fill=1)

    def build(self, laudo_data):
        doc = SimpleDocTemplate(
            self.buffer, pagesize=A4, rightMargin=15*mm, leftMargin=15*mm, topMargin=35*mm, bottomMargin=20*mm
        )
        story = []
        
        story.append(Spacer(1, 5*mm))
        story.append(Paragraph(f"EMPRESA: {self.company.nome_fantasia.upper()}", self.styles['OrgTitle']))
        story.append(Paragraph(f"CNPJ: {self.company.cnpj}", self.styles['OrgSubtitle']))
        story.append(Spacer(1, 8*mm))

        idx = laudo_data.get('overall_avg', 0)
        total_resp = laudo_data.get('total_respondentes', 0)
        overall_class = laudo_data.get('overall_classification', '')
        
        metrics_data = [
            [
             Paragraph(f"<font color='#64748b' size=8>RESPONDENTES</font><br/><b>{total_resp}</b>", self.styles['Normal']),
             Paragraph(f"<font color='#64748b' size=8>MÉDIA GERAL</font><br/><b>{idx} / 5.0</b>", self.styles['Normal']),
             Paragraph(f"<font color='white' size=8>CLASSIFICAÇÃO GERAL</font><br/><font color='white' size=12><b>{saxutils.escape(overall_class)}</b></font>", self.styles['Normal'])
            ]
        ]
        metrics_table = Table(metrics_data, colWidths=[60*mm, 60*mm, 60*mm])
        metrics_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (1, 0), COL_SLATE_50),
            ('BACKGROUND', (2, 0), (2, 0), COL_BLUE),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.white),
            ('BOX', (0, 0), (-1, -1), 0.5, COL_SLATE_100),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(metrics_table)
        story.append(Spacer(1, 8*mm))

        chart_data = laudo_data.get('chart_data', {})
        radar_dict = chart_data.get('radar', {})
        if len(radar_dict) >= 3:
            class DummyRadar(Flowable):
                def __init__(self, rl, r_dict):
                    Flowable.__init__(self)
                    self.rl = rl
                    self.r_dict = r_dict
                    self.width = 180*mm
                    self.height = 75*mm
                def draw(self):
                    self.rl._draw_radar(self.canv, self.width / 2.0, self.height / 2.0, self.r_dict)
            story.append(DummyRadar(self, radar_dict))
            story.append(Spacer(1, 6*mm))

        risk_matrix = laudo_data.get('risk_matrix', [])
        if risk_matrix:
            story.append(Paragraph("1. Matriz de Risco Organizacional por Vetor e Dimensão", self.styles['Heading2']))
            story.append(_build_vetor_dimension_table(self.styles, risk_matrix))
            story.append(Spacer(1, 8*mm))

        sesmt = laudo_data.get('sesmt', {})
        if sesmt:
            story.append(Paragraph("2. Camada SESMT — Integração Normativa", self.styles['Heading2']))
            pgr = sesmt.get('pgr_gro', {})
            story.append(Paragraph(f"<b>PGR/GRO:</b> {pgr.get('total_riscos', 0)} riscos ({pgr.get('riscos_criticos', 0)} críticos)", self.styles['Normal']))
            nr17 = sesmt.get('nr17', {})
            story.append(Paragraph(f"<b>NR-17 (Ergonomia):</b> {saxutils.escape(nr17.get('achado', ''))}", self.styles['Normal']))
            nr12 = sesmt.get('nr12', {})
            story.append(Paragraph(f"<b>NR-12 (Segurança):</b> {saxutils.escape(nr12.get('achado', ''))}", self.styles['Normal']))
            story.append(Spacer(1, 8*mm))

        story.append(Paragraph("3. Conclusão Pericial", self.styles['Heading2']))
        conclusao = laudo_data.get('conclusao', '')
        if conclusao:
            story.append(Paragraph(saxutils.escape(conclusao), self.styles['Normal']))
            story.append(Spacer(1, 8*mm))

        references = laudo_data.get('references', [])
        if references:
            story.append(Spacer(1, 8*mm))
            story.append(Paragraph("4. Bibliografia e Rastreabilidade", self.styles['Heading3']))
            ref_p = []
            for r in references[:5]:
                ref_p.append(f"\u2022 {saxutils.escape(r)}")
            if ref_p:
                story.append(Paragraph("<br/>".join(ref_p), self.styles['Normal']))

        story.append(Spacer(1, 15*mm))
        story.append(Paragraph("________________________________________________", self.styles['Normal']))
        story.append(Paragraph("<font size=8 color='#64748b'>Documento Pericial gerado eletronicamente via Motor de Análise SIMDCCONR01</font>", self.styles['Normal']))

        doc.build(story, onFirstPage=self._draw_header, onLaterPages=self._draw_header)

def html_to_pdf(html_string, base_url=None):
    """Deprecated."""
    return None, "Use RespondentReportRL ou DepartmentReportRL."
