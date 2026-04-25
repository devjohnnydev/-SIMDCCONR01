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
from django.conf import settings

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.pdfgen import canvas
from reportlab.platypus import Flowable

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
        logo_width = 0
        if self._logo_image_data:
            try:
                from reportlab.lib.utils import ImageReader
                img_reader = ImageReader(io.BytesIO(self._logo_image_data))
                img_w, img_h = img_reader.getSize()
                logo_width = (12*mm / img_h) * img_w
                canvas.drawImage(img_reader, 15*mm, 270*mm, height=12*mm,
                                 preserveAspectRatio=True, mask='auto')
                logo_drawn = True
            except Exception as e:
                logger.warning(f"Erro ao desenhar logo no header: {e}")

        # SEMPRE mostrar o nome SIMDCCONR01 (ao lado do logo ou sozinho)
        if logo_drawn:
            # Logo presente: nome ao lado, menor
            canvas.setFont('Helvetica-Bold', 12)
            canvas.setFillColor(COL_BLUE)
            canvas.drawString(15*mm + logo_width + 4*mm, 272*mm, "SIMDCCONR01")
        else:
            # Sem logo: nome grande como fallback
            canvas.setFont('Helvetica-Bold', 18)
            canvas.setFillColor(COL_BLUE)
            canvas.drawString(15*mm, 272*mm, "SIMDCCONR01")

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
            lx = x + (max_r + 8*mm)*math.cos(rad)
            ly = y + (max_r + 8*mm)*math.sin(rad)
            label_txt = labels[i][:18] + ".." if len(labels[i]) > 18 else labels[i]
            canvas.drawCentredString(lx, ly, label_txt.upper())

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

    def build(self, report_data, sections):
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
             Paragraph(f"<font color='#64748b' size=7>DATA DA AVALIAÇÃO</font><br/><b>{self.generated_at.strftime('%d/%m/%Y %H:%M')}</b>", self.styles['Normal'])],
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
        # 4. RELATÓRIO ESTRUTURADO (sem PageBreak!)
        # ═══════════════════════════════════════════════
        story.append(Paragraph("Relatório Estruturado", self.styles['Heading2']))

        for section in sections:
            # Header da seção
            section_label = saxutils.escape(f"{section['meta']['number']}. {section['meta']['label']}")
            story.append(Paragraph(section_label, self.styles['SectionHeading']))

            # Texto Qualitativo
            if section.get('text'):
                safe_text = saxutils.escape(section['text'])
                safe_text = safe_text.replace('\n', '<br/>')
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
                ts = self.diagnostic.signature_timestamp.strftime('%d/%m/%Y %H:%M')

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
        logo_width = 0
        if self._logo_image_data:
            try:
                from reportlab.lib.utils import ImageReader
                img_reader = ImageReader(io.BytesIO(self._logo_image_data))
                img_w, img_h = img_reader.getSize()
                logo_width = (12*mm / img_h) * img_w
                canvas.drawImage(img_reader, 15*mm, 270*mm, height=12*mm, preserveAspectRatio=True, mask='auto')
                logo_drawn = True
            except: pass
        
        canvas.setFont('Helvetica-Bold', 12 if logo_drawn else 18)
        canvas.setFillColor(COL_BLUE)
        x_pos = 15*mm + (logo_width + 4*mm if logo_drawn else 0)
        canvas.drawString(x_pos, 272*mm, "SIMDCCONR01")

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

    def build(self, data):
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
        metrics_data = [
            [Paragraph(f"<font color='#64748b' size=8>DEPARTAMENTO</font><br/><b>{self.diagnostic.setor}</b>", self.styles['Normal']),
             Paragraph(f"<font color='#64748b' size=8>DATA GERAÇÃO</font><br/><b>{self.generated_at.strftime('%d/%m/%Y')}</b>", self.styles['Normal']),
             Paragraph(f"<font color='white' size=8>BEM-ESTAR DO GRUPO</font><br/><font color='white' size=14><b>{idx}%</b></font>", self.styles['Normal'])]
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
        story.append(Spacer(1, 10*mm))

        # 3. Sumário do Clima Geral
        story.append(Paragraph("1. Sumário do Clima Geral", self.styles['Heading2']))
        story.append(Paragraph(saxutils.escape(data.get('clima_geral', '')), self.styles['Normal']))
        story.append(Spacer(1, 8*mm))

        # 4. Pontos Fortes e Alertas
        story.append(Paragraph("2. Análise Detalhada", self.styles['Heading2']))
        
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
        story.append(Paragraph("3. Recomendações Estratégicas para o Gestor", self.styles['Heading2']))
        for i, s in enumerate(data.get('sugestoes_gestao', []), 1):
            story.append(Paragraph(f"<b>{i}.</b> {saxutils.escape(s)}", self.styles['Normal']))
            story.append(Spacer(1, 3*mm))

        # Autenticação
        story.append(Spacer(1, 15*mm))
        story.append(Paragraph("________________________________________________", self.styles['Normal']))
        story.append(Paragraph("<font size=8 color='#64748b'>Documento gerado eletronicamente via Motor de Análise SIMDCCONR01</font>", self.styles['Normal']))
        story.append(Paragraph(f"<font size=7 color='#94a3b8'>ID: {self.diagnostic.id} | Timestamp: {self.generated_at.isoformat()}</font>", self.styles['Normal']))

        doc.build(story, onFirstPage=self._draw_header, onLaterPages=self._draw_header)


def html_to_pdf(html_string, base_url=None):
    """Deprecated."""
    return None, "Use RespondentReportRL ou DepartmentReportRL."
