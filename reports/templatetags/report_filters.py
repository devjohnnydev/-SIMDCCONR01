from django import template
from django.utils.safestring import mark_safe
import json

register = template.Library()

@register.filter
def format_ai_data(value):
    if not value: return ""
    
    if isinstance(value, str):
        # Maybe it's a JSON string representing list/dict
        if value.strip().startswith('[') or value.strip().startswith('{'):
            try:
                value = json.loads(value)
            except json.JSONDecodeError:
                pass

    if isinstance(value, list):
        items = "".join([f"<li class='mb-2'>{item}</li>" for item in value])
        return mark_safe(f"<ul class='mb-0 ps-3'>{items}</ul>")
    
    if isinstance(value, dict):
        lines = []
        for k, v in value.items():
            k_fmt = str(k).replace('_', ' ').title()
            lines.append(f"<b>{k_fmt}:</b> {v}")
        return mark_safe("<br/><br/>".join(lines))
    
    # Just normal string
    return mark_safe(str(value).replace('\n', '<br/>'))
