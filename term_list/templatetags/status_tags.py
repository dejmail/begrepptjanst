from django import template
from pdb import set_trace
register = template.Library()

@register.filter
def status_colour(status_label, config):
    """
    Given a status label and the config dict,
    return the colour associated with the label.
    """
    try:
        statuses = config.get("statuses", [])
        for item in statuses:
            if item.get("label").strip() == status_label.strip():
                return item.get("colour", "#ccc")  # default fallback colour
    except Exception:
        pass
    return "#ccc"  # fallback colour
