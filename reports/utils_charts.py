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
        if value == 0: continue
        
        angle = (value / total) * 360
        color = colors[i % len(colors)]
        
        # Coordenadas do arco
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
    
    # Adicionar furo central branco
    svg.append(f'<circle cx="{cx}" cy="{cy}" r="{inner_r}" fill="white" />')
    
    # Adicionar legenda ou total no centro
    svg.append(f'<text x="{cx}" y="{cy}" text-anchor="middle" dominant-baseline="middle" font-family="Arial" font-size="{size*0.1}" font-weight="bold">{int(total)}</text>')
    
    svg.append('</svg>')
    return "".join(svg)
