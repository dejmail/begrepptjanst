from django import template
from django.template.defaulttags import register
from pdb import set_trace

register = template.Library()

@register.simple_tag(name="config_filter")
def config_filter(**kwargs):

    attribute = kwargs.get('attribute')
    attribute_value = kwargs.get('attribute_value')
    queryset = kwargs.get('queryset').filter(**{attribute: attribute_value})
    
    return queryset.first()