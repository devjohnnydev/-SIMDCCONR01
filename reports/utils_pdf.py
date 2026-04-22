"""
==================================================================================
UTILS PDF (FPDF2) — Pure Python PDF Generation for SIMDCCONR01
==================================================================================
Este módulo substitui o WeasyPrint/xhtml2pdf para eliminar dependências de C.
Garante funcionamento 100% estável em ambientes Railway/Replit.
"""
import os
import math
import logging
from fpdf import FPDF
from django.utils import timezone

logger = logging.getLogger(__name__)

class RespondentReportPDF(FPDF):
    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop('company', None)
        self.generated_at = kwargs.pop('generated_at', timezone.now())
        super().__init__(*args, **kwargs)
        self.set_auto_page_break(auto=True, margin=15)
        self.add_page()
        
    def header(self):
        # Background Logo / Header
        if self.page_no() == 1:
            # Logo placeholder ou real
            self.set_font('helvetica', 'B', 16)
            self.set_text_color(37, 99, 235) # blue-600
            
            if self.company and self.company.logo and os.path.exists(self.company.logo.path):
                self.image(self.company.logo.path, 10, 10, h=12)
                self.set_x(10)
            else:
                self.text(10, 18, "SIMDCCONR01")
            
            self.set_font('helvetica', 'B', 12)
            self.set_text_color(15, 23, 42) # slate-900
            self.cell(0, 10, 'Parecer Técnico Pericial', align='R', ln=True)
            self.set_font('helvetica', '', 8)
            self.set_text_color(100, 116, 139) # slate-500
            self.cell(0, 5, 'DOCUMENTO OFICIAL · RASTREABILIDADE TOTAL', align='R', ln=True)
            
            # Linha azul superior
            self.set_draw_color(37, 99, 235)
            self.set_line_width(0.8)
            self.line(10, 27, 200, 27)
            self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.set_text_color(148, 163, 184)
        self.cell(0, 10, f'Página {self.page_no()} de {{nb}} — Parecer Técnico SIMDCCONR01', align='C')

    def draw_info_card(self, employee, diagnostic):
        self.set_fill_color(248, 250, 252)
        self.set_draw_color(226, 232, 240)
        self.set_line_width(0.2)
        
        # Card Background
        self.rect(10, self.get_y(), 190, 35, 'DF')
        
        y_start = self.get_y() + 5
        self.set_x(15)
        
        # Row 1
        self.set_font('helvetica', 'B', 7)
        self.set_text_color(100, 116, 139)
        self.text(15, y_start, "FUNCIONÁRIO")
        self.text(140, y_start, "CPF")
        
        self.set_font('helvetica', 'B', 10)
        self.set_text_color(15, 23, 42)
        self.text(15, y_start + 5, employee.nome.upper())
        self.text(140, y_start + 5, employee.cpf or "Não informado")
        
        # Row 2
        y_row2 = y_start + 12
        self.set_font('helvetica', 'B', 7)
        self.set_text_color(100, 116, 139)
        self.text(15, y_row2, "EMPRESA")
        self.text(140, y_row2, "DATA DE EMISSÃO")
        
        self.set_font('helvetica', 'B', 9)
        self.set_text_color(15, 23, 42)
        self.text(15, y_row2 + 5, (self.company.nome_fantasia if self.company else "S/I").upper())
        self.text(140, y_row2 + 5, self.generated_at.strftime('%d/%m/%Y %H:%M'))
        
        # Row 3
        y_row3 = y_row2 + 12
        self.set_font('helvetica', 'B', 7)
        self.set_text_color(100, 116, 139)
        self.text(15, y_row3, "SETOR / FUNÇÃO")
        
        self.set_font('helvetica', 'B', 9)
        self.set_text_color(15, 23, 42)
        self.text(15, y_row3 + 5, f"{employee.setor} — {employee.cargo}")
        
        self.set_y(y_start + 30)
        self.ln(10)

    def draw_radar_chart(self, dimension_summary):
        """Desenha um gráfico radar matemático diretamente no PDF."""
        self.set_font('helvetica', 'B', 10)
        self.set_text_color(71, 85, 105)
        self.cell(0, 10, "SÍNTESE DO PERFIL OCUPACIONAL", align='C', ln=True)
        
        cx, cy = 105, self.get_y() + 45
        max_r = 35
        max_val = 5.0
        
        data = {dim['dimensao']: dim['media'] for dim in dimension_summary if dim.get('instrumento') == 'IMCO'}
        if not data: return
        
        labels = list(data.keys())
        values = list(data.values())
        n = len(labels)
        
        # Desenhar círculos do grid
        self.set_draw_color(224, 224, 224)
        self.set_line_width(0.1)
        for level in range(1, 6):
            r = max_r * (level / max_val)
            self.ellipse(cx - r, cy - r, 2*r, 2*r)
            
        # Eixos e Labels
        self.set_font('helvetica', '', 6)
        angles = [(i * 360 / n) - 90 for i in range(n)]
        for i, angle_deg in enumerate(angles):
            rad = math.radians(angle_deg)
            x_end = cx + max_r * math.cos(rad)
            y_end = cy + max_r * math.sin(rad)
            self.line(cx, cy, x_end, y_end)
            
            # Label
            label_x = cx + (max_r + 8) * math.cos(rad)
            label_y = cy + (max_r + 8) * math.sin(rad)
            txt = labels[i][:15] + ".." if len(labels[i]) > 15 else labels[i]
            self.text(label_x - 5, label_y, txt)

        # Polígono de Dados
        points = []
        for i, val in enumerate(values):
            r = max_r * (min(val, max_val) / max_val)
            rad = math.radians(angles[i])
            points.append((cx + r * math.cos(rad), cy + r * math.sin(rad)))
        
        self.set_draw_color(37, 99, 235)
        self.set_line_width(0.5)
        self.set_fill_color(37, 99, 235)
        # polyline/polygon manual
        for i in range(len(points)):
            p1 = points[i]
            p2 = points[(i + 1) % len(points)]
            self.line(p1[0], p1[1], p2[0], p2[1])
            self.circle(p1[0], p1[1], 1, 'F')
            
        self.set_y(cy + 45)

    def render_section(self, section):
        if self.get_y() > 220: self.add_page()
        
        # Header da Seção
        self.set_fill_color(15, 23, 42) # Slate 900
        self.set_text_color(255, 255, 255)
        self.set_font('helvetica', 'B', 11)
        self.cell(0, 10, f" {section['meta']['number']}. {section['meta']['label']}", ln=True, fill=True)
        
        # Texto da Análise
        if section['text']:
            self.ln(3)
            self.set_fill_color(241, 245, 249)
            self.set_draw_color(37, 99, 235)
            self.set_line_width(0.5)
            
            y_before = self.get_y()
            self.set_font('helvetica', '', 10)
            self.set_text_color(51, 65, 85)
            
            # Multi_cell para o texto longo
            self.multi_cell(0, 6, section['text'], border='L', fill=True, align='J')
            self.ln(5)

        # Tabela de Itens
        self.set_font('helvetica', 'B', 7)
        self.set_fill_color(248, 250, 252)
        self.set_text_color(71, 85, 105)
        
        col_widths = [20, 80, 50, 15, 25]
        headers = ['ID', 'ITEM / PERGUNTA', 'REFERÊNCIA', 'VAL.', 'STATUS']
        
        for i, h in enumerate(headers):
            self.cell(col_widths[i], 8, h, border=1, fill=True, align='C')
        self.ln()
        
        self.set_font('helvetica', '', 8)
        self.set_text_color(15, 23, 42)
        
        for item in section['items']:
            if self.get_y() > 260:
                self.add_page()
                # Re-print headers optionally if needed, but for simplicity:
            
            start_y = self.get_y()
            # ID
            self.cell(col_widths[0], 10, str(item['id_item']), border=1, align='C')
            # Pergunta (usando multi_cell para wrap)
            curr_x = self.get_x()
            self.multi_cell(col_widths[1], 5, item['pergunta'], border=1)
            end_y = self.get_y()
            h = end_y - start_y
            
            # Voltar para preencher as outras colunas da linha se o wrap foi grande
            self.set_y(start_y)
            self.set_x(10 + col_widths[0] + col_widths[1])
            
            # Referência
            self.multi_cell(col_widths[2], 5, f"{item['constructo']}\n{item['autor']} ({item['ano']})", border=1)
            self.set_y(start_y)
            self.set_x(10 + col_widths[0] + col_widths[1] + col_widths[2])
            
            # Valor
            self.cell(col_widths[3], h, str(item['valor'] or "-"), border=1, align='C')
            # Status
            self.cell(col_widths[4], h, item['classificacao'], border=1, align='C')
            
            self.set_y(max(self.get_y(), end_y))
        
        self.ln(10)

    def draw_signature(self, diagnostic):
        if self.get_y() > 200: self.add_page()
        self.ln(10)
        
        cx = 105
        self.set_draw_color(15, 23, 42)
        self.line(cx - 40, self.get_y() + 15, cx + 40, self.get_y() + 15)
        
        if diagnostic.is_signed and diagnostic.signer_profile:
            sig = diagnostic.signer_profile
            if sig.signature_image and os.path.exists(sig.signature_image.path):
                self.image(sig.signature_image.path, cx - 35, self.get_y(), h=12)
        
        self.ln(18)
        self.set_font('helvetica', 'B', 10)
        self.set_text_color(15, 23, 42)
        name = "Aguardando Assinatura"
        if diagnostic.signer_profile: name = diagnostic.signer_profile.nome_completo
        elif diagnostic.signed_by: name = diagnostic.signed_by.get_full_name()
        
        self.cell(0, 5, name, align='C', ln=True)
        
        self.set_font('helvetica', '', 8)
        self.set_text_color(100, 116, 139)
        spec = "Especialista em Saúde Ocupacional"
        if diagnostic.signer_profile: spec = f"{diagnostic.signer_profile.get_especialidade_display()} — {diagnostic.signer_profile.registro_profissional}"
        self.cell(0, 5, spec, align='C', ln=True)
        
        if diagnostic.is_signed:
            self.set_text_color(22, 101, 52)
            self.ln(2)
            self.set_font('helvetica', 'B', 8)
            self.cell(0, 5, f"AUTENTICADO EM {diagnostic.signature_timestamp.strftime('%d/%m/%Y %H:%M')}", align='C', ln=True)

    def draw_bibliography(self, references, validation_code):
        self.ln(10)
        self.set_fill_color(248, 250, 252)
        self.set_draw_color(226, 232, 240)
        self.rect(10, self.get_y(), 190, 40, 'FD')
        
        self.set_y(self.get_y() + 3)
        self.set_x(15)
        self.set_font('helvetica', 'B', 8)
        self.set_text_color(71, 85, 105)
        self.cell(0, 5, "BIBLIOGRAFIA E RASTREABILIDADE (MODELO FDAC)", ln=True)
        
        self.set_font('helvetica', '', 7)
        self.set_text_color(100, 116, 139)
        for ref in references[:4]: # Mantendo compacto no PDF
            self.set_x(15)
            self.cell(0, 4, f"• {ref[:120]}...", ln=True)
            
        self.ln(2)
        self.set_font('helvetica', 'B', 7)
        self.cell(0, 5, f"Autenticação: {validation_code} | SIMDCCONR01", align='C', ln=True)

def html_to_pdf(html_string, base_url=None):
    """Fallback: Não usado mais para o laudo individual, pois migramos para RespondentReportPDF."""
    return None, "Deprecated. Use RespondentReportPDF class."
