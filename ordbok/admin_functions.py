from django.contrib import admin
from django.db.models import Q, Count
from django.utils.safestring import mark_safe
from django.contrib.auth.models import Group
from .models import Dictionary, Begrepp

def add_non_breaking_space_to_status(status_item):

    length = len(status_item)
    length_to_add = 12 - length
    for x in range(length_to_add):
        if x % 2 == 0:
            status_item += '&nbsp;'
        else:
            status_item = '&nbsp;' + status_item
    return mark_safe(status_item)

class DictionaryRestrictedAdminMixin:
    """
    A mixin that restricts access to objects based on the user's group
    memberships and their relation to dictionaries.
    """

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        user_groups = request.user.groups.all()
        return qs.filter(Q(dictionaries__groups__in=user_groups)).distinct()

class DictionaryRestrictedOtherModelAdminMixin:
    """
    A mixin that restricts access to objects based on the user's group
    memberships and their relation to dictionaries.
    """

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs

        user_groups = request.user.groups.all()

        # Filter dictionaries that are accessible to the user's groups
        accessible_dictionaries = Dictionary.objects.filter(
            groups__in=user_groups
        ).distinct()

        # Filter the queryset based on the accessible dictionaries
        return qs.filter(begrepp__dictionaries__in=accessible_dictionaries).distinct()


class DictionaryFilter(admin.SimpleListFilter):
    title = 'Ordbok'
    parameter_name = 'ordbok'

    def lookups(self, request, model_admin):
        # Returns a list of tuples. The first element in each tuple is the coded value for the option that will appear in the URL query. The second element is the human-readable name for the option that will appear in the right sidebar.
        dictionaries = Dictionary.objects.values('dictionary_name').annotate(name_count=Count('dictionary_name')).filter(name_count__gt=0).distinct()
        lookups = [(dictionary['dictionary_name'], dictionary['dictionary_name']) for dictionary in dictionaries]
        lookups.append(('no_dictionary', 'Inga Ordböcker'))
        return  lookups

    def queryset(self, request, queryset):
        if self.value() == 'no_dictionary':
            # Filter for Begrepp instances without an associated Dictionary
            return queryset.filter(dictionaries__isnull=True)
        elif self.value():
            # Filter for Begrepp instances with the selected Dictionary name
            return queryset.filter(dictionaries__dictionary_name=self.value())
        return queryset
