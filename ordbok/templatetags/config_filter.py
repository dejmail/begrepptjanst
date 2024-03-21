from django import template
from django.template.defaulttags import register
from django.db.models.query import QuerySet
from pdb import set_trace

register = template.Library()

@register.simple_tag(name="config_filter")
def config_filter(**kwargs):

    attribute = kwargs.get('attribute')
    attribute_value = kwargs.get('attribute_value')
    queryset = kwargs.get('queryset')
    
    if type(queryset) == QuerySet:
        # Need to return a first otherwise it's a list of items and we only want one anyway
        return queryset.filter(**{attribute: attribute_value}).first()
    else:
        return queryset
    