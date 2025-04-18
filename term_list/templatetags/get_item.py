from django.template.defaulttags import register
from django import template
from pdb import set_trace

register = template.Library()

@register.filter(name='get_item')
def get_item(dictionary, key):
    return dictionary.get(key)