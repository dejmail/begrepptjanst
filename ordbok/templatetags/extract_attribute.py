from django import template
from pdb import set_trace

register = template.Library()

@register.simple_tag
def extract_attribute(**kwargs):
    
    target_id = kwargs.get('target_id')
    queryset = kwargs.get('queryset')
    attribute = kwargs.get('attribute')

    matching_object = queryset.filter(id=target_id).first()
    if matching_object:
        return getattr(matching_object, attribute, None)
    return None