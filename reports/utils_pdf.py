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
        self.alias_nb_pages()
        
        # Metadados de segurança
        self.set_author('Plataforma SIMDCCONR01')
        self.set_subject('Parecer Técnico Pericial de Diagnóstico')
        self.set_creator('SIMDCCONR01 - Engine v2')
        
    def _t(self, text):
        """Sanitiza texto para encoding Latin-1 (padrão FPDF core fonts)."""
        if text is None: return ""
        # Remove caracteres de controle que podem corromper o PDF
        clean_text = "".join(ch for ch in str(text) if ch.isprintable() or ch in "\n\r\t")
        # Substituições comuns de Unicode não suportadas pelo Latin-1
        replacements = {
            '\u2014': '-', # em-dash
            '\u2013': '-', # en-dash
            '\u2022': '*', # bullet
            '\u2026': '...', # ellipsis
            '\xa0': ' ',    # non-breaking space
        }
        for k, v in replacements.items():
            clean_text = clean_text.replace(k, v)
            
        return clean_text.encode('latin-1', 'replace').decode('latin-1')
        
    def header(self):
        # Logo placeholder ou real
        self.set_font('helvetica', 'B', 16)
        self.set_text_color(37, 99, 235) # blue-600
        
        logo_path = None
        if self.company and self.company.logo:
            try:
                if os.path.exists(self.company.logo.path):
                    logo_path = self.company.logo.path
            except: pass

        if logo_path:
            try:
                self.image(logo_path, 10, 10, h=12)
            except:
                self.text(10, 18, self._t("SIMDCCONR01"))
        else:
            self.text(10, 18, self._t("SIMDCCONR01"))
        
        self.set_font('helvetica', 'B', 12)
        self.set_text_color(15, 23, 42) # slate-900
        self.cell(0, 10, self._t('Parecer Técnico Pericial'), align='R', ln=True)
        self.set_font('helvetica', '', 8)
        self.set_text_color(100, 116, 139) # slate-500
        self.cell(0, 5, self._t('DOCUMENTO OFICIAL · RASTREABILIDADE TOTAL'), align='R', ln=True)
        
        # Linha azul superior
        self.set_draw_color(37, 99, 235)
        self.set_line_width(0.8)
        self.line(10, 27, 200, 27)
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.set_text_color(148, 163, 184)
        # {nb} será substituído pelo alias_nb_pages
        self.cell(0, 10, self._t(f'Página {self.page_no()} de {{nb}} - Parecer Técnico SIMDCCONR01'), align='C')

    def draw_info_card(self, employee, diagnostic):
        if self.get_y() > 240: self.add_page()
        
        self.set_fill_color(248, 250, 252)
        self.set_draw_color(226, 232, 240)
        self.set_line_width(0.2)
        
        self.rect(10, self.get_y(), 190, 35, 'DF')
        y_start = self.get_y() + 5
        
        self.set_font('helvetica', 'B', 7)
        self.set_text_color(100, 116, 139)
        self.text(15, y_start, self._t("FUNCIONÁRIO"))
        self.text(140, y_start, self._t("CPF"))
        
        self.set_font('helvetica', 'B', 10)
        self.set_text_color(15, 23, 42)
        self.text(15, y_start + 5, self._t(employee.nome.upper()))
        self.text(140, y_start + 5, self._t(employee.cpf or "Não informado"))
        
        y_row2 = y_start + 12
        self.set_font('helvetica', 'B', 7)
        self.set_text_color(100, 116, 139)
        self.text(15, y_row2, self._t("EMPRESA"))
        self.text(140, y_row2, self._t("DATA DE EMISSÃO"))
        
        self.set_font('helvetica', 'B', 9)
        self.set_text_color(15, 23, 42)
        comp_name = self.company.nome_fantasia if self.company else "S/I"
        self.text(15, y_row2 + 5, self._t(comp_name.upper()))
        self.text(140, y_row2 + 5, self.generated_at.strftime('%d/%m/%Y %H:%M'))
        
        y_row3 = y_row2 + 12
        self.set_font('helvetica', 'B', 7)
        self.set_text_color(100, 116, 139)
        self.text(15, y_row3, self._t("SETOR / FUNÇÃO"))
        
        self.set_font('helvetica', 'B', 9)
        self.set_text_color(15, 23, 42)
        self.text(15, y_row3 + 5, self._t(f"{employee.setor} - {employee.cargo}"))
        
        self.set_y(y_start + 30)
        self.ln(10)

    def draw_radar_chart(self, dimension_summary):
        if self.get_y() > 200: self.add_page()
        
        self.set_font('helvetica', 'B', 10)
        self.set_text_color(71, 85, 105)
        self.cell(0, 10, self._t("SÍNTESE DO PERFIL OCUPACIONAL"), align='C', ln=True)
        
        cx, cy = 105, self.get_y() + 45
        max_r = 35
        max_val = 5.0
        
        data = {}
        for dim in dimension_summary:
            if dim.get('instrumento') == 'IMCO':
                data[dim['dimensao']] = dim.get('media', 0)
                
        if not data: return
        labels = list(data.keys())
        values = list(data.values())
        n = len(labels)
        if n < 3: return
        
        self.set_draw_color(224, 224, 224)
        self.set_line_width(0.1)
        for level in range(1, 6):
            r = max_r * (level / max_val)
            self.ellipse(cx - r, cy - r, 2*r, 2*r)
            
        self.set_font('helvetica', '', 6)
        angles = [(i * 360 / n) - 90 for i in range(n)]
        for i, angle_deg in enumerate(angles):
            rad = math.radians(angle_deg)
            x_end = cx + max_r * math.cos(rad)
            y_end = cy + max_r * math.sin(rad)
            self.line(cx, cy, x_end, y_end)
            
            label_dist = max_r + 8
            label_x = cx + label_dist * math.cos(rad)
            label_y = cy + label_dist * math.sin(rad)
            txt = labels[i][:15] + ".." if len(labels[i]) > 15 else labels[i]
            self.text(label_x - 5, label_y, self._t(txt))

        points = []
        for i, val in enumerate(values):
            r = max_r * (min(val, max_val) / max_val)
            rad = math.radians(angles[i])
            points.append((cx + r * math.cos(rad), cy + r * math.sin(rad)))
        
        self.set_draw_color(37, 99, 235)
        self.set_line_width(0.5)
        self.set_fill_color(37, 99, 235)
        for i in range(len(points)):
            p1 = points[i]
            p2 = points[(i + 1) % len(points)]
            self.line(p1[0], p1[1], p2[0], p2[1])
            self.circle(p1[0], p1[1], 1, 'F')
            
        self.set_y(cy + 45)

    def render_section(self, section):
        if self.get_y() > 220: self.add_page()
        
        self.set_fill_color(15, 23, 42)
        self.set_text_color(255, 255, 255)
        self.set_font('helvetica', 'B', 11)
        self.cell(0, 10, self._t(f" {section['meta']['number']}. {section['meta']['label']}"), ln=True, fill=True)
        
        if section.get('text'):
            self.ln(3)
            self.set_fill_color(241, 245, 249)
            self.set_draw_color(37, 99, 235)
            self.set_line_width(0.5)
            self.set_font('helvetica', '', 10)
            self.set_text_color(51, 65, 85)
            self.multi_cell(0, 6, self._t(section['text']), border='L', fill=True, align='J')
            self.ln(5)

        self.set_font('helvetica', 'B', 7)
        self.set_fill_color(248, 250, 252)
        self.set_text_color(71, 85, 105)
        
        col_widths = [15, 85, 45, 15, 30]
        headers = ['ID', 'ITEM / PERGUNTA', 'REFERÊNCIA', 'VAL.', 'STATUS']
        
        for i, h in enumerate(headers):
            self.cell(col_widths[i], 8, self._t(h), border=1, fill=True, align='C')
        self.ln()
        
        self.set_font('helvetica', '', 8)
        self.set_text_color(15, 23, 42)
        
        for item in section.get('items', []):
            if self.get_y() > 250: self.add_page()
            
            start_y = self.get_y()
            # Multi-cell for item description
            self.set_x(10 + col_widths[0])
            self.multi_cell(col_widths[1], 5, self._t(item.get('pergunta', '-')), border=1)
            end_y_desc = self.get_y()
            
            # Multi-cell for reference
            self.set_y(start_y)
            self.set_x(10 + col_widths[0] + col_widths[1])
            ref_txt = f"{item.get('constructo', '')} ({item.get('ano', '')})"
            self.multi_cell(col_widths[2], 5, self._t(ref_txt), border=1)
            end_y_ref = self.get_y()
            
            h = max(end_y_desc, end_y_ref) - start_y
            
            # Fill other columns with fixed height
            self.set_y(start_y)
            self.set_x(10)
            self.cell(col_widths[0], h, self._t(item.get('id_item', '-')), border=1, align='C')
            self.set_x(10 + col_widths[0] + col_widths[1] + col_widths[2])
            self.cell(col_widths[3], h, self._t(item.get('valor') or "-"), border=1, align='C')
            self.cell(col_widths[4], h, self._t(item.get('classificacao', '-')), border=1, align='C')
            
            self.set_y(start_y + h)
        
        self.ln(10)

    def draw_signature(self, diagnostic):
        if self.get_y() > 200: self.add_page()
        self.ln(10)
        cx = 105
        self.set_draw_color(15, 23, 42)
        self.line(cx - 40, self.get_y() + 15, cx + 40, self.get_y() + 15)
        
        sig_path = None
        if diagnostic.is_signed and diagnostic.signer_profile:
            sig = diagnostic.signer_profile
            try:
                if sig.signature_image and os.path.exists(sig.signature_image.path):
                    sig_path = sig.signature_image.path
            except: pass

        if sig_path:
            try:
                self.image(sig_path, cx - 35, self.get_y(), h=12)
            except: pass
        
        self.ln(18)
        self.set_font('helvetica', 'B', 10)
        self.set_text_color(15, 23, 42)
        name = "Aguardando Assinatura"
        if diagnostic.signer_profile: name = diagnostic.signer_profile.nome_completo
        elif diagnostic.signed_by: name = diagnostic.signed_by.get_full_name()
        
        self.cell(0, 5, self._t(name), align='C', ln=True)
        self.set_font('helvetica', '', 8)
        self.set_text_color(100, 116, 139)
        spec = "Especialista em Saúde Ocupacional"
        if diagnostic.signer_profile: spec = f"{diagnostic.signer_profile.get_especialidade_display()} - {diagnostic.signer_profile.registro_profissional}"
        self.cell(0, 5, self._t(spec), align='C', ln=True)
        
        if diagnostic.is_signed:
            self.set_text_color(22, 101, 52)
            self.ln(2)
            ts = diagnostic.signature_timestamp or timezone.now()
            self.set_font('helvetica', 'B', 8)
            self.cell(0, 5, self._t(f"AUTENTICADO EM {ts.strftime('%d/%m/%Y %H:%M')}"), align='C', ln=True)

    def draw_bibliography(self, references, validation_code):
        if not references: return
        if self.get_y() > 240: self.add_page()
        self.ln(5)
        self.set_fill_color(248, 250, 252)
        self.set_draw_color(226, 232, 240)
        self.rect(10, self.get_y(), 190, 35, 'FD')
        
        self.set_y(self.get_y() + 2)
        self.set_x(15)
        self.set_font('helvetica', 'B', 8)
        self.set_text_color(71, 85, 105)
        self.cell(0, 5, self._t("BIBLIOGRAFIA E RASTREABILIDADE (MODELO FDAC)"), ln=True)
        
        self.set_font('helvetica', '', 7)
        self.set_text_color(100, 116, 139)
        for ref in references[:3]:
            self.set_x(15)
            self.cell(0, 4, self._t(f"* {ref[:120]}..."), ln=True)
            
        self.ln(2)
        self.set_font('helvetica', 'B', 7)
        self.cell(0, 5, self._t(f"Autenticação: {validation_code} | SIMDCCONR01"), align='C', ln=True)

def html_to_pdf(html_string, base_url=None):
    return None, "Deprecated."
