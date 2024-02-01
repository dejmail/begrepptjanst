from django import template
from django.template.defaulttags import register
from django.db.models.query import QuerySet

register = template.Library()

@register.simple_tag(name="config_filter")
def config_filter(**kwargs):

    attribute = kwargs.get('attribute')
    attribute_value = kwargs.get('attribute_value')
    queryset = kwargs.get('queryset')
    
    if type(queryset) == QuerySet:
        queryset.filter(**{attribute: attribute_value})
        return queryset.first()
    else:
        return queryset