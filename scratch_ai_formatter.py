def format_ai_data(data):
    if not data: return ""
    if isinstance(data, str): return data
    if isinstance(data, list):
        return "\n".join([f"• {item}" for item in data])
    if isinstance(data, dict):
        lines = []
        for k, v in data.items():
            k_fmt = str(k).replace('_', ' ').title()
            lines.append(f"{k_fmt}: {v}")
        return "\n".join(lines)
    return str(data)
