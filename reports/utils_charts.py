"""
==================================================================================
UTILS CHARTS — SVG Chart Generation for SIMDCCONR01 Reports
==================================================================================
Gera gráficos SVG embeddáveis em PDFs via WeasyPrint.
Inclui: Radar, Heatmap, Barras (Likert), Pie/Donut.
==================================================================================
"""
import math


def generate_pie_chart_svg(data, size=200, colors=None):
    """
    Gera um SVG de gráfico de rosca (donut chart) a partir de um dicionário {'Rótulo': Valor}.
    Ideal para inclusão em PDFs via WeasyPrint.
    """
    if not colors:
        colors = ['#2e7d32', '#f9a825', '#c62828', '#212121', '#1565c0']

    total = sum(data.values())
    if total == 0:
        return ""

    cx, cy = size / 2, size / 2
    r = size * 0.4
    thickness = size * 0.15
    inner_r = r - thickness

    svg = [f'<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}" xmlns="http://www.w3.org/2000/svg">']

    current_angle = 0
    for i, (label, value) in enumerate(data.items()):
        if value == 0:
            continue

        angle = (value / total) * 360
        color = colors[i % len(colors)]

        start_angle = current_angle
        end_angle = current_angle + angle

        x1 = cx + r * math.cos(math.radians(start_angle - 90))
        y1 = cy + r * math.sin(math.radians(start_angle - 90))
        x2 = cx + r * math.cos(math.radians(end_angle - 90))
        y2 = cy + r * math.sin(math.radians(end_angle - 90))

        ix1 = cx + inner_r * math.cos(math.radians(start_angle - 90))
        iy1 = cy + inner_r * math.sin(math.radians(start_angle - 90))
        ix2 = cx + inner_r * math.cos(math.radians(end_angle - 90))
        iy2 = cy + inner_r * math.sin(math.radians(end_angle - 90))

        large_arc = 1 if angle > 180 else 0

        path = (
            f'M {x1} {y1} '
            f'A {r} {r} 0 {large_arc} 1 {x2} {y2} '
            f'L {ix2} {iy2} '
            f'A {inner_r} {inner_r} 0 {large_arc} 0 {ix1} {iy1} Z'
        )

        svg.append(f'<path d="{path}" fill="{color}"><title>{label}: {value}</title></path>')
        current_angle += angle

    svg.append(f'<circle cx="{cx}" cy="{cy}" r="{inner_r}" fill="white" />')
    svg.append(
        f'<text x="{cx}" y="{cy}" text-anchor="middle" dominant-baseline="middle" '
        f'font-family="Arial" font-size="{size * 0.1}" font-weight="bold">{int(total)}</text>'
    )

    svg.append('</svg>')
    return "".join(svg)


def generate_radar_chart_svg(data, size=300, color='#1565c0'):
    """
    Gera um SVG de gráfico radar (spider chart).

    Args:
        data: dict {'Dimensão': valor_medio} — valores de 0 a 5.
        size: tamanho do SVG em pixels.
        color: cor de preenchimento da área.
    Returns:
        string SVG.
    """
    if not data:
        return ""

    labels = list(data.keys())
    values = list(data.values())
    n = len(labels)

    if n < 3:
        return ""

    cx, cy = size / 2, size / 2
    max_r = size * 0.38
    label_r = size * 0.46
    max_val = 5.0

    svg = [
        f'<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}" '
        f'xmlns="http://www.w3.org/2000/svg" style="font-family: Arial, sans-serif;">'
    ]

    # Grid circles (níveis 1 a 5)
    for level in range(1, 6):
        r = max_r * (level / max_val)
        svg.append(
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" '
            f'stroke="#e0e0e0" stroke-width="0.5"/>'
        )
        # Nível label
        svg.append(
            f'<text x="{cx + 3}" y="{cy - r + 4}" font-size="8" fill="#999">{level}</text>'
        )

    # Axes
    angles = [(i * 360 / n) - 90 for i in range(n)]
    for i, angle_deg in enumerate(angles):
        x = cx + max_r * math.cos(math.radians(angle_deg))
        y = cy + max_r * math.sin(math.radians(angle_deg))
        svg.append(
            f'<line x1="{cx}" y1="{cy}" x2="{x}" y2="{y}" '
            f'stroke="#ccc" stroke-width="0.5"/>'
        )

    # Data polygon
    points = []
    for i, val in enumerate(values):
        r = max_r * (min(val, max_val) / max_val)
        x = cx + r * math.cos(math.radians(angles[i]))
        y = cy + r * math.sin(math.radians(angles[i]))
        points.append(f"{x},{y}")

    polygon_str = " ".join(points)
    svg.append(
        f'<polygon points="{polygon_str}" fill="{color}" fill-opacity="0.25" '
        f'stroke="{color}" stroke-width="2"/>'
    )

    # Data points
    for i, val in enumerate(values):
        r = max_r * (min(val, max_val) / max_val)
        x = cx + r * math.cos(math.radians(angles[i]))
        y = cy + r * math.sin(math.radians(angles[i]))
        svg.append(f'<circle cx="{x}" cy="{y}" r="4" fill="{color}"/>')

    # Labels
    for i, label in enumerate(labels):
        x = cx + label_r * math.cos(math.radians(angles[i]))
        y = cy + label_r * math.sin(math.radians(angles[i]))

        anchor = 'middle'
        if math.cos(math.radians(angles[i])) > 0.3:
            anchor = 'start'
        elif math.cos(math.radians(angles[i])) < -0.3:
            anchor = 'end'

        # Truncar labels longas
        display_label = label[:18] + '…' if len(label) > 18 else label

        svg.append(
            f'<text x="{x}" y="{y}" text-anchor="{anchor}" '
            f'dominant-baseline="middle" font-size="9" fill="#333">'
            f'{display_label}</text>'
        )

    svg.append('</svg>')
    return "".join(svg)


def generate_heatmap_svg(data, width=400, row_height=40):
    """
    Gera um SVG de heatmap de risco por departamento.

    Args:
        data: dict {'Departamento': {'score': float, 'classificacao': str}}
        width: largura do SVG.
        row_height: altura de cada linha.
    Returns:
        string SVG.
    """
    if not data:
        return ""

    n = len(data)
    height = n * row_height + 60  # header + rows

    color_map = {
        'Crítico': '#c62828',
        'Atenção': '#f9a825',
        'Adequado': '#43a047',
        'Forte': '#1565c0',
    }

    label_width = width * 0.4
    bar_width = width * 0.45
    score_width = width * 0.15

    svg = [
        f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
        f'xmlns="http://www.w3.org/2000/svg" style="font-family: Arial, sans-serif;">'
    ]

    # Header
    svg.append(
        f'<text x="10" y="20" font-size="12" font-weight="bold" fill="#333">'
        f'Mapa de Risco por Departamento</text>'
    )
    svg.append(
        f'<line x1="0" y1="30" x2="{width}" y2="30" stroke="#ccc" stroke-width="1"/>'
    )

    y = 40
    for dept, info in sorted(data.items(), key=lambda x: x[1].get('score', 0)):
        score = info.get('score', 0)
        classificacao = info.get('classificacao', 'Adequado')
        color = color_map.get(classificacao, '#999')

        # Department label
        display_dept = dept[:20] + '…' if len(dept) > 20 else dept
        svg.append(
            f'<text x="10" y="{y + row_height * 0.6}" font-size="11" fill="#333">'
            f'{display_dept}</text>'
        )

        # Bar
        bar_pct = min(score / 5.0, 1.0)
        bar_actual = bar_width * bar_pct
        svg.append(
            f'<rect x="{label_width}" y="{y + 5}" width="{bar_actual}" '
            f'height="{row_height - 10}" rx="3" fill="{color}" fill-opacity="0.8"/>'
        )

        # Score
        svg.append(
            f'<text x="{label_width + bar_width + 10}" y="{y + row_height * 0.6}" '
            f'font-size="11" font-weight="bold" fill="{color}">'
            f'{score:.1f}</text>'
        )

        y += row_height

    # Legend
    y += 10
    for label, color in color_map.items():
        svg.append(
            f'<rect x="10" y="{y}" width="12" height="12" rx="2" fill="{color}"/>'
        )
        svg.append(
            f'<text x="28" y="{y + 10}" font-size="9" fill="#666">{label}</text>'
        )
        y += 18

    svg.append('</svg>')
    return "".join(svg)


def generate_bar_chart_svg(data, width=400, height=200, color='#1565c0'):
    """
    Gera um SVG de gráfico de barras para distribuição Likert.

    Args:
        data: dict {1: count, 2: count, 3: count, 4: count, 5: count}
        width: largura do SVG.
        height: altura do SVG.
        color: cor das barras.
    Returns:
        string SVG.
    """
    if not data:
        return ""

    labels = sorted(data.keys())
    values = [data[k] for k in labels]
    max_val = max(values) if values else 1

    n = len(labels)
    margin_left = 50
    margin_bottom = 40
    margin_top = 20
    chart_width = width - margin_left - 20
    chart_height = height - margin_bottom - margin_top
    bar_spacing = chart_width / n
    bar_width = bar_spacing * 0.6

    likert_colors = {
        1: '#c62828',  # Discordo totalmente
        2: '#ef6c00',  # Discordo
        3: '#f9a825',  # Neutro
        4: '#43a047',  # Concordo
        5: '#1565c0',  # Concordo totalmente
    }

    likert_labels = {
        1: 'Discordo\nTotalmente',
        2: 'Discordo',
        3: 'Neutro',
        4: 'Concordo',
        5: 'Concordo\nTotalmente',
    }

    svg = [
        f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
        f'xmlns="http://www.w3.org/2000/svg" style="font-family: Arial, sans-serif;">'
    ]

    # Y-axis gridlines
    num_gridlines = 5
    for i in range(num_gridlines + 1):
        y = margin_top + chart_height - (chart_height * i / num_gridlines)
        val = int(max_val * i / num_gridlines)
        svg.append(
            f'<line x1="{margin_left}" y1="{y}" x2="{width - 20}" y2="{y}" '
            f'stroke="#eee" stroke-width="1"/>'
        )
        svg.append(
            f'<text x="{margin_left - 5}" y="{y + 4}" text-anchor="end" '
            f'font-size="9" fill="#999">{val}</text>'
        )

    # Bars
    for i, (label, value) in enumerate(zip(labels, values)):
        bar_h = (value / max_val) * chart_height if max_val > 0 else 0
        x = margin_left + i * bar_spacing + (bar_spacing - bar_width) / 2
        y = margin_top + chart_height - bar_h

        bar_color = likert_colors.get(label, color)

        svg.append(
            f'<rect x="{x}" y="{y}" width="{bar_width}" height="{bar_h}" '
            f'rx="3" fill="{bar_color}" fill-opacity="0.85">'
            f'<title>{label}: {value}</title></rect>'
        )

        # Value on top
        svg.append(
            f'<text x="{x + bar_width / 2}" y="{y - 5}" text-anchor="middle" '
            f'font-size="10" font-weight="bold" fill="{bar_color}">{value}</text>'
        )

        # Label below
        lbl = str(label)
        svg.append(
            f'<text x="{x + bar_width / 2}" y="{margin_top + chart_height + 15}" '
            f'text-anchor="middle" font-size="9" fill="#666">{lbl}</text>'
        )

    svg.append('</svg>')
    return "".join(svg)
