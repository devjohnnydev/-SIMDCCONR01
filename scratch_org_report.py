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
            lx = x + (max_r + 8*mm)*math.cos(rad)
            ly = y + (max_r + 8*mm)*math.sin(rad)
            label_txt = labels[i][:18] + ".." if len(labels[i]) > 18 else labels[i]
            canvas.drawCentredString(lx, ly, label_txt.upper())

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
            story.append(Paragraph("1. Matriz de Risco Organizacional", self.styles['Heading2']))
            
            matrix_data = [['INSTR.', 'DIMENSÃO', 'MÉDIA', 'CLASSIFICAÇÃO', 'RISCO (PGR)']]
            col_widths = [18*mm, 65*mm, 15*mm, 35*mm, 45*mm]
            
            for item in risk_matrix:
                status = item.get('classificacao', '-')
                matrix_data.append([
                    Paragraph(f"<font size=7 color='#2563eb'>{item.get('instrumento', '')}</font>", self.styles['Normal']),
                    Paragraph(f"<font size=8>{saxutils.escape(item.get('dimensao', ''))}</font>", self.styles['Normal']),
                    Paragraph(f"<font size=8>{item.get('media', '-')}</font>", self.styles['Normal']),
                    Paragraph(f"<font size=8><b>{saxutils.escape(status)}</b></font>", self.styles['Normal']),
                    Paragraph(f"<font size=7 color='#64748b'>{saxutils.escape(item.get('risco', '-'))}</font>", self.styles['Normal']),
                ])
                
            matrix_table = Table(matrix_data, colWidths=col_widths, repeatRows=1)
            matrix_table_style = [
                ('BACKGROUND', (0, 0), (-1, 0), COL_DARK),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('INNERGRID', (0, 0), (-1, -1), 0.25, COL_SLATE_100),
                ('BOX', (0, 0), (-1, -1), 0.5, COL_SLATE_100),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
            ]
            
            for row_idx in range(1, len(matrix_data)):
                it = risk_matrix[row_idx - 1]
                clr = colors.transparent
                if it.get('classificacao_key') == 'critico': clr = COL_DANGER
                elif it.get('classificacao_key') == 'atencao': clr = COL_WARNING
                elif it.get('classificacao_key') == 'adequado': clr = COL_SUCCESS
                matrix_table_style.append(('BACKGROUND', (3, row_idx), (3, row_idx), clr))
                
            matrix_table.setStyle(TableStyle(matrix_table_style))
            story.append(matrix_table)
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

