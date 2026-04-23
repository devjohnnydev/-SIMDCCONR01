"""
==================================================================================
UTILS PDF (REPORTLAB) — Industrial Standard PDF Generation for SIMDCCONR01
==================================================================================
Este módulo substitui o FPDF2 para garantir total compatibilidade com visualizadores
de PDF modernos (Chrome/Edge) e eliminar erros de segurança de carregamento.
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

from reportlab.platypus import Flowable

class RadarChartFlowable(Flowable):
    def __init__(self, respondent_report_rl, dimension_summary, width=120*mm, height=80*mm):
        Flowable.__init__(self)
        self.width = width
        self.height = height
        self.dimension_summary = dimension_summary
        self.rr = respondent_report_rl

    def draw(self):
        # Center horizontally within the width provided, and vertically
        self.rr._draw_radar(self.canv, self.width / 2.0, self.height / 2.0, self.dimension_summary)

class RespondentReportRL:
    def __init__(self, buffer, company=None, diagnostic=None):
        self.buffer = buffer
        self.company = company
        self.diagnostic = diagnostic
        self.generated_at = timezone.now()
        self.styles = getSampleStyleSheet()
        self._setup_styles()
        
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
        canvas.saveState()
        
        # Logo
        logo_path = None
        if self.company and self.company.logo:
            try:
                if os.path.exists(self.company.logo.path):
                    logo_path = self.company.logo.path
            except: pass
            
        if logo_path:
            canvas.drawImage(logo_path, 15*mm, 270*mm, height=12*mm, preserveAspectRatio=True, mask='auto')
        else:
            canvas.setFont('Helvetica-Bold', 18)
            canvas.setFillColor(COL_BLUE)
            canvas.drawString(15*mm, 272*mm, "SIMDCCONR01")
            
        # Title Block
        canvas.setFont('Helvetica-Bold', 14)
        canvas.setFillColor(COL_DARK)
        canvas.drawRightString(195*mm, 275*mm, "Parecer Técnico Pericial")
        
        canvas.setFont('Helvetica-Bold', 7)
        canvas.setFillColor(COL_BLUE)
        canvas.drawRightString(195*mm, 271*mm, "DOCUMENTO OFICIAL · RASTREABILIDADE TOTAL")
        
        # Line
        canvas.setStrokeColor(COL_BLUE)
        canvas.setLineWidth(0.8)
        canvas.line(15*mm, 268*mm, 195*mm, 268*mm)
        
        # Footer
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
        
        # 1. Title
        story.append(Spacer(1, 5*mm))
        story.append(Paragraph("SÍNTESE DE RESULTADOS", self.styles['ReportTitle']))
        story.append(Paragraph("ANÁLISE DE SAÚDE MENTAL E CLIMA", self.styles['ReportSubtitle']))
        story.append(Spacer(1, 10*mm))
        
        # 2. Info Card (Tabela Estilizada)
        emp = self.diagnostic.assignment.employee
        info_data = [
            [Paragraph(f"<font color='#64748b' size=7>FUNCIONÁRIO</font><br/><b>{emp.nome.upper()}</b>", self.styles['Normal']),
             Paragraph(f"<font color='#64748b' size=7>CPF</font><br/><b>{emp.cpf or 'Não informado'}</b>", self.styles['Normal'])],
            [Paragraph(f"<font color='#64748b' size=7>EMPRESA</font><br/><b>{self.company.nome_fantasia.upper() if self.company else '-'}</b>", self.styles['Normal']),
             Paragraph(f"<font color='#64748b' size=7>DATA DA AVALIAÇÃO</font><br/><b>{self.generated_at.strftime('%d/%m/%Y %H:%M')}</b>", self.styles['Normal'])],
            [Paragraph(f"<font color='#64748b' size=7>SETOR E CARGO</font><br/><b>{emp.setor} — {emp.cargo}</b>", self.styles['Normal']), ""]
        ]
        info_table = Table(info_data, colWidths=[110*mm, 70*mm])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), COL_SLATE_50),
            ('BORDER', (0, 0), (-1, -1), 0.5, COL_SLATE_100),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.white),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('SPAN', (0, 2), (1, 2)),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ]))
        story.append(info_table)
        story.append(Spacer(1, 15*mm))
        
        # 3. Radar Chart (now as a flowable, no more random spacing)
        story.append(RadarChartFlowable(self, report_data.get('dimension_summary', []), width=180*mm, height=75*mm))
        story.append(Spacer(1, 10*mm))
        
        # 4. Relatório Estruturado
        story.append(PageBreak())
        story.append(Paragraph("Relatório Estruturado", self.styles['Heading2']))
        
        for section in sections:
            # Header
            story.append(Paragraph(f"{section['meta']['number']}. {section['meta']['label']}", self.styles['SectionHeading']))
            
            # Texto Qualitativo
            if section.get('text'):
                safe_text = saxutils.escape(section['text'])
                # Replace newlines with <br/> for ReportLab
                safe_text = safe_text.replace('\n', '<br/>')
                story.append(Paragraph(safe_text, self.styles['AnalysisBox']))
                story.append(Spacer(1, 10))
                
            # Tabela de Itens
            item_data = [['ID', 'ITEM / PERGUNTA', 'REF.', 'VAL.', 'STATUS']]
            col_widths = [15*mm, 85*mm, 35*mm, 15*mm, 30*mm]
            
            for item in section.get('items', []):
                ref = f"{item.get('constructo', '')}\n({item.get('ano', '')})"
                status = item.get('classificacao', '-')
                
                # Cores de Status
                status_color = colors.transparent
                if item.get('classificacao_key') == 'critico': status_color = COL_DANGER
                elif item.get('classificacao_key') == 'atencao': status_color = COL_WARNING
                elif item.get('classificacao_key') == 'adequado': status_color = COL_SUCCESS
                
                safe_pergunta = saxutils.escape(item.get('pergunta', '-')).replace('\n', '<br/>')
                safe_ref = saxutils.escape(ref).replace('\n', '<br/>')
                
                item_data.append([
                    Paragraph(f"<font color='#64748b'>{item.get('id_item', '-')}</font>", self.styles['Normal']),
                    Paragraph(safe_pergunta, self.styles['Normal']),
                    Paragraph(f"<font size=7 color='#64748b'>{safe_ref}</font>", self.styles['Normal']),
                    Paragraph(str(item.get('valor') or "-"), self.styles['Normal']),
                    Paragraph(f"<b>{status}</b>", self.styles['Normal'])
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
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
            ]
            
            # Colorir celula de status por linha
            for row_idx in range(1, len(item_data)):
                # Identificar status_color baseado na lógica acima
                # (precisamos repetir a lógica de cor aqui para o TableStyle)
                it = section['items'][row_idx - 1]
                clr = colors.transparent
                if it.get('classificacao_key') == 'critico': clr = COL_DANGER
                elif it.get('classificacao_key') == 'atencao': clr = COL_WARNING
                elif it.get('classificacao_key') == 'adequado': clr = COL_SUCCESS
                items_table_style.append(('BACKGROUND', (4, row_idx), (4, row_idx), clr))
                
            items_table.setStyle(TableStyle(items_table_style))
            story.append(items_table)
            story.append(Spacer(1, 15))

        # 4. Assinatura & Bibliografia
        story.append(PageBreak())
        
        # Assinatura (Lógica Refatorada)
        sig_data = [["____________________________________"], ["Aguardando Assinatura Eletrônica"]]
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
            
            # 2. Tentar imagem do SignerProfile via .open()
            elif signer and getattr(signer, 'signature_image', None):
                try:
                    with signer.signature_image.open('rb') as f:
                        sig_img = Image(io.BytesIO(f.read()), width=50*mm, height=15*mm)
                except Exception as e:
                    logger.error(f"Erro image signature (signer): {e}")
                    
            # 3. Tentar imagem do User via .open()
            elif user_signer and getattr(user_signer, 'signature_image', None):
                try:
                    with user_signer.signature_image.open('rb') as f:
                        sig_img = Image(io.BytesIO(f.read()), width=50*mm, height=15*mm)
                except Exception as e:
                    logger.error(f"Erro image signature (user): {e}")

            # Define Name and Spec
            if signer:
                name = signer.nome_completo
                spec = f"{signer.get_especialidade_display()} — {signer.registro_profissional}"
            elif user_signer:
                name = user_signer.get_full_name()
                crp = user_signer.professional_crp
                spec = f"Profissional Especializado{' — ' + crp if crp else ''}"
            else:
                name = "Assinado Digitalmente"
                spec = ""
                
            ts = self.diagnostic.signature_timestamp.strftime('%d/%m/%Y %H:%M') if self.diagnostic.signature_timestamp else ""
            
            sig_data = [[sig_img if sig_img else ""], [f"<b>{name}</b>"], [spec], [f"Autenticado em {ts}"]]

        sig_table = Table(sig_data, colWidths=[100*mm])
        sig_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ]))
        story.append(Spacer(1, 30*mm))
        story.append(sig_table)
        
        # Bibliografia
        story.append(Spacer(1, 20*mm))
        story.append(Paragraph("5. Bibliografia e Rastreabilidade (Modelo FDAC)", self.styles['Heading3']))
        ref_p = []
        for r in report_data.get('references', [])[:5]:
            safe_r = saxutils.escape(r)
            ref_p.append(f"• {safe_r}")
        story.append(Paragraph("<br/>".join(ref_p), self.styles['Normal']))
        
        story.append(Spacer(1, 15))
        story.append(Paragraph(f"<font size='7' color='#64748b'>Código de Autenticação: {self.diagnostic.validation_code}</font>", self.styles['Normal']))

        # Metadata final
        doc.title = f"Laudo {emp.nome}"
        doc.author = "SIMDCCONR01"

        # Final Build com o Canvas customizado
        try:
            # We don't draw the radar in onFirstPage anymore, it's a Flowable!
            doc.build(story, 
                onFirstPage=self._draw_header,
                onLaterPages=self._draw_header
            )
        except Exception as e:
            logger.error(f"Erro no build do ReportLab: {e}")
            raise e

def html_to_pdf(html_string, base_url=None):
    """Deprecated."""
    return None, "Use RespondentReportRL."
