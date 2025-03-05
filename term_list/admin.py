import re
from pdb import set_trace
import logging

from django import forms
from django.conf import settings
from django.contrib import admin
from django.db.models import Case, IntegerField, Q, Value, When, Count
from django.db.models.functions import Lower
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django_admin_multiple_choice_list_filter.list_filters import \
    MultipleChoiceListFilter
from rangefilter.filters import DateRangeFilter, DateTimeRangeFilter
from simple_history.admin import SimpleHistoryAdmin
from django.http import HttpResponse

from term_list.forms import (
    ConceptForm, 
    AttributeValueInlineForm
    # AttributeValueInlineFormSet
    )
from term_list.models import *
from django.conf import settings

from term_list import admin_actions
from term_list.forms import ConceptExternalFilesForm, ChooseExportAttributes
from term_list.admin_actions import (change_dictionaries,
                                  export_chosen_begrepp_attrs_action)

from django.core.files.uploadedfile import InMemoryUploadedFile

admin.site.site_header = """OLLI Begreppstjänst Admin
 För fakta i livet"""
admin.site.site_title = "OLLI Begpreppstjänst Admin Portal"
admin.site.index_title = "Välkommen till OLLI Begreppstjänst Portalen"

from term_list.admin_functions import (DictionaryRestrictAdminMixin,
                                    DictionaryRestrictedOtherModelAdminMixin,
                                    ConceptFileImportMixin,
                                    DictionaryFilter,
                                    DuplicateTermFilter,
                                    add_non_breaking_space_to_status)                             

logger = logging.getLogger(__name__)

class SynonymInlineForm(forms.ModelForm):

    class Meta:
        model = Synonym
        fields = "__all__"

    def clean(self):
        super(SynonymInlineForm, self).clean()
        if self.cleaned_data.get('synonym') == None:
            self.add_error('synonym', 'Kan inte radera synonym med bak knappen, använder checkbox till höger')

class SynonymInline(admin.StackedInline):

    model = Synonym
    form = SynonymInlineForm
    extra = 1

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        formset.form.user = request.user  # Pass the user to the form
        return formset

class ConceptExternalFilesInline(admin.StackedInline):

    model = ConceptExternalFiles
    extra = 1
    verbose_name = "Externt Kontext Fil"
    verbose_name_plural = "Externa Kontext Filer"

class StatusListFilter(MultipleChoiceListFilter):
    title = 'Status'
    template = "admin/multiple_status_filter.html"
    parameter_name = 'status__in'
    
    def lookups(self, request, model_admin):
        return STATUS_CHOICES

class ExcelImportForm(forms.Form):
    excel_file = forms.FileField()

class TaskOrdererAdmin(DictionaryRestrictAdminMixin, admin.ModelAdmin):

    list_display = ('name',
                    'email',
                    'create_date',
                    'finished_by_date',
                    'term')
    search_fields = ("term__term","name", "email") 

    def term(self, obj):
        
        display_text = [
        f"<a href='{reverse('admin:{}_{}_change'.format(obj._meta.app_label, obj._meta.related_objects[0].name), args=(concept.id,))}'>{concept.term}</a>"
        for concept in obj.concepts.all()
        ]        
        if display_text:
            return mark_safe(", ".join(display_text))   

class DictionaryAdmin(DictionaryRestrictAdminMixin, admin.ModelAdmin):

    list_display = ('dictionary_name',
                    'dictionary_id',
                    'dictionary_context',
                    'order')

    list_filter = ("dictionary_name",)
    #search_fields = ('begrepp__term',)

class SynonymAdmin(DictionaryRestrictedOtherModelAdminMixin, admin.ModelAdmin):
    
    ordering = ['concept__term']
    list_display = ('concept',
                    # 'begrepp',
                    'synonym',
                    'synonym_status')

    list_select_related = (
        'concept',
    )
    list_filter = ("synonym_status",)
    search_fields = ("concept__term", "synonym")

class ConceptExternalFileForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.label_suffix = ""  # Removes the ":" after the label



class ContextFilesInline(admin.StackedInline):

    model = ConceptExternalFiles
    form = ConceptExternalFileForm
    extra = 1
    verbose_name = "Externt Kontext Fil"
    verbose_name_plural = "Externa Kontext Filer"
    readonly_fields = ['concept',]


class ConceptCommentsAdmin(DictionaryRestrictedOtherModelAdminMixin, 
                             admin.ModelAdmin):

    class Media:
        css = {

            'all': ('https://use.fontawesome.com/releases/v5.8.2/css/all.css',
                   f'{settings.STATIC_URL}css/admin_kommentarmodel_custom.css',
                   f'{settings.STATIC_URL}css/custom_icon.css')
            }

    inlines = [ContextFilesInline,]

    list_display = ('concept',
                    'usage_context',
                    'attached_files',
                    'date',
                    'email',
                    'name',
                    'status'
                    )

    list_filter = ('status',)

    readonly_fields = ['date',]

    fieldsets = [
        ['Main', {
        'fields': [('concept', 'date'), 
        ('usage_context',), 
        ('email','name','status'),]},
        ]]

    def attached_files(self, obj):

        if (obj.conceptexternalfiles_set.exists()) and (obj.conceptexternalfiles_set.name != ''):
            return format_html(f'''<a href={obj.conceptexternalfiles_set}>
                                    <i class="fas fa-file-download">
                                    </i>
                                    </a>''')
        else:
            return format_html(f'''<span style="color: red;">            
                                       <i class="far fa-times-circle"></i>
                                    </span>''')
    attached_files.short_description = "Bifogade filer"

    def save_formset(self, request, form, formset, change):
        
        if request.method == 'POST':
            instances = formset.save(commit=False)
            for instance in instances:
                if not instance.begrepp_id:
                    instance.begrepp_id = form.cleaned_data.get('concept').pk
                instance.save()
        formset.save_m2m()

class MetadataSearchTrackAdmin(admin.ModelAdmin):

    list_display = ('sök_term',
                    'ip_adress',
                    'sök_timestamp')

class SearchTrackAdmin(admin.ModelAdmin):

    list_display = ('sök_term',
                    'ip_adress',
                    'sök_timestamp',
                    'records_returned')

class ConceptExternalFilesAdmin(DictionaryRestrictedOtherModelAdminMixin, 
                                admin.ModelAdmin):

    model = ConceptExternalFiles
    form = ConceptExternalFilesForm

    list_display = ('concept', 'comment', 'support_file')

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "kommentar":
            # Filter the queryset for the ForeignKey field based on the user's group
            user_groups = request.user.groups.all()
            kwargs["queryset"] = ConceptComment.objects.filter(
            begrepp__begrepp_fk__groups__in=user_groups
            ).distinct()

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

class ConfigurationOptionsAdmin(admin.ModelAdmin):
    
    model = ConfigurationOptions

class AttributeValueInline(admin.StackedInline):
    model = AttributeValue
    form = AttributeValueInlineForm
    extra = 0
    can_delete = False
    template = "admin/edit_inline/stacked.html" 

    def has_add_permission(self, request, obj=None):
        return False  # ✅ Prevents the 'Add another' button from appearing

class ConceptAdmin(DictionaryRestrictAdminMixin,
                   ConceptFileImportMixin,
                   SimpleHistoryAdmin):

    model = Concept
    class Media:
        css = {
        'all': (
            f'{settings.STATIC_URL}css/main.css',
            f'{settings.STATIC_URL}css/begrepp_custom.css',
           )
         }
        
    # Below is not working
    change_form_template = 'begrepp_change_form.html'
    change_list_template = "begrepp_changelist.html"

    list_display = ['term', 'definition', 'status_button', 'list_dictionaries']
    search_fields = ('term',
                    'definition',
                    'synonyms__synonym',
                    )
    
    list_filter = (StatusListFilter,
                   ('changed_at', DateRangeFilter),
                   'dictionaries',
                   DuplicateTermFilter
    )
    
    inlines = [AttributeValueInline]

    def status_button(self, obj):
        status_classes = {
        'Avråds': 'tag tag-avrådd text-monospace',
        'Avrådd': 'tag tag-avrådd text-monospace',
        'Avställd': 'tag tag-avrådd text-monospace',
        'Publicera ej': 'tag tag-light-blue text-monospace dark-text',
        'Pågår': 'tag tag-oklart light-text text-monospace',
        'Ej Påbörjad': 'tag tag-oklart light-text text-monospace',
        'Beslutad': 'tag tag-grön light-text text-monospace'
        }

        css_class = status_classes.get(obj.status, 'tag btn-white dark-text text-monospace')
        
        display_text = f'<span class="{css_class}">{add_non_breaking_space_to_status(obj.status)}</span>'
        return mark_safe(display_text)

    status_button.short_description = 'Status'

    def get_inlines(self, request, obj=None):
        """
        Conditionally return inlines only when editing an existing Concept.
        """
        if obj:  # Only show inlines when editing an existing instance
            return [AttributeValueInline]
        return []
    
    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        concept = self.get_object(request, object_id)
        
        if concept:
            # Filter attributes based on the Concept's dictionary
            
            # extra_context['filtered_attributes'] = Attribute.objects.filter(
            #     groups__dictionaries__dictionary_long_name=concept.dictionaries
            #     )
            
            extra_context['filtered_attributes'] = Attribute.objects.filter(
            groups__dictionaries__in=concept.dictionaries.all()
            )
        
        return super().change_view(request, object_id, form_url, extra_context=extra_context)
    
    def get_queryset(self, request):

        """
        Annotate the search where the search string is found in different connected
        models. Done so that the search results are more relevant.
        """

        queryset = super().get_queryset(request)

        if request.GET.get('q'):
            search_term = request.GET.get('q')
            queryset = queryset.annotate(
                position=Case(
                    When(Q(term__iexact=search_term), then=Value(1)),
                    When(Q(term__istartswith=search_term), then=Value(2)),
                    When(Q(term__icontains=search_term), then=Value(3)),
                    When(Q(synonyms__synonym__icontains=search_term), then=Value(4)),
                    When(Q(definition__icontains=search_term), then=Value(5)),
                    default=Value(0),
                    output_field=IntegerField()
                )
            ).order_by('position')
        return queryset
    
    # def get_form(self, request, obj=None, **kwargs):
    #     """
    #     Dynamically modify the admin form to include attribute fields BEFORE calling super().
    #     """
    #     # ✅ Retrieve default form class but do not initialize it yet
    #     form_class = super().get_form(request, obj, **kwargs)

    #     if obj:  # ✅ Only modify the form if editing an existing Concept
    #         logger.debug(f"Generating dynamic fields for Concept: {obj}")

    #         # ✅ Retrieve dynamically added attributes
    #         dynamic_fields = {
    #             f"attribute_{attr.id}": forms.CharField(label=attr.display_name, required=False)
    #             for attr in Attribute.objects.all()
    #         }

    #         # ✅ Create a new form class dynamically by adding fields
    #         class DynamicConceptForm(form_class):
    #             pass

    #         for field_name, field in dynamic_fields.items():
    #             setattr(DynamicConceptForm, field_name, field)  # ✅ Add each field dynamically

    #         return DynamicConceptForm  # ✅ Return the dynamically created form class

    #     return form_class
    
    # def get_fieldsets(self, request, obj=None):
    #     """
    #     Dynamically generate fieldsets based on available attributes.
    #     """
    #     fieldsets = super().get_fieldsets(request, obj)  # ✅ Get default fieldsets

    #     if obj:
    #         logger.debug(f"Generating dynamic fieldsets for Concept: {obj}")

    #         # ✅ Retrieve dynamically added attributes
    #         dynamic_fields = [f"attribute_{attr.id}" for attr in Attribute.objects.all()]
    #         if dynamic_fields:
    #             fieldsets += (("Dynamic Attributes", {"fields": dynamic_fields}),)  # ✅ Append dynamically generated fields

    #     return fieldsets
    
    
    def save_model(self, request, obj, form, change):
        """
        Save the Concept instance first.
        """
        logger.debug(f"POST data received: {request.POST}")
        super().save_model(request, obj, form, change)


    def save_related(self, request, form, formsets, change):
        """
        After saving the Concept and its ManyToMany relationships,
        create the appropriate AttributeValue instances.
        """
        super().save_related(request, form, formsets, change)

        # Now that ManyToMany relationships are saved, proceed with AttributeValues
        concept = form.instance  # Get the current Concept instance
        
        if concept.dictionaries.exists():
            # Step 1: Get all related Group IDs from the selected Dictionaries
            group_ids = concept.dictionaries.values_list('groups__id', flat=True)
            
            # Step 2: Fetch all Attributes linked to those Groups
            relevant_attributes = Attribute.objects.filter(groups__id__in=group_ids).distinct()
            
            # Step 3: Create AttributeValue objects for each Attribute
            for attribute in relevant_attributes:
                AttributeValue.objects.get_or_create(
                    term=concept,  # Link to the current Concept instance
                    attribute=attribute
                )
    
    def list_dictionaries(self, obj):
        return ", ".join([dictionary.dictionary_name for dictionary in obj.dictionaries.all()])

    list_dictionaries.short_description = 'term_list'
    list_dictionaries.verbose = 'Ordböcker'

class AttributeAdmin(admin.ModelAdmin):

    list_display = ['display_name', 'data_type', 'description', 'list_groups']

    def list_groups(self, obj):
        return ", ".join([group.name for group in obj.groups.all()])

class AttributeValueAdmin(admin.ModelAdmin):

    model = AttributeValue

    list_display = ['term', 'attribute__display_name', 'get_value']

    search_fields = [
    'term__term',
    'attribute__display_name',
    'value_string',
    'value_text',
    'value_integer',
    'value_decimal',
    'value_boolean',
    'value_url',
    ]
    
    def get_queryset(self, request):

        """
        Assign a rank to the search so that the most relevant are presented 
        first
        """

        queryset = super().get_queryset(request)

        if request.GET.get('q'):
            search_term = request.GET.get('q')
            queryset = queryset.annotate(
                position=Case(
                    # Search in term fields
                    When(Q(term__term__iexact=search_term), then=Value(1)),
                    When(Q(term__term__istartswith=search_term), then=Value(2)),
                    When(Q(term__term__icontains=search_term), then=Value(3)),

                    # Search in definition field
                    When(Q(term__definition__icontains=search_term), then=Value(4)),

                    When(Q(attribute__display_name__icontains=search_term), then=Value(5)),

                    # Search in value_* fields
                    When(Q(value_string__icontains=search_term), then=Value(6)),
                    When(Q(value_text__icontains=search_term), then=Value(7)),
                    When(Q(value_integer__icontains=search_term), then=Value(8)),
                    When(Q(value_decimal__icontains=search_term), then=Value(9)),
                    When(Q(value_boolean__icontains=search_term), then=Value(10)),
                    When(Q(value_url__icontains=search_term), then=Value(11)),

                    default=Value(0),
                    output_field=IntegerField()
                )
            ).order_by('position')
        return queryset

class GroupAttributeAdmin(admin.ModelAdmin):

    list_display = ['group__name', 'attribute__display_name', 'position']

# admin.site.register(Begrepp, BegreppAdmin)
# admin.site.register(TaskOrderer, TaskOrdererAdmin)
admin.site.register(Dictionary, DictionaryAdmin)
admin.site.register(Synonym, SynonymAdmin)
admin.site.register(ConceptComment, ConceptCommentsAdmin)
admin.site.register(SearchTrack, SearchTrackAdmin)
admin.site.register(MetadataSearchTrack, MetadataSearchTrackAdmin)
admin.site.register(ConceptExternalFiles,ConceptExternalFilesAdmin)
admin.site.register(ConfigurationOptions, ConfigurationOptionsAdmin)
admin.site.register(Concept, ConceptAdmin)
admin.site.register(Attribute, AttributeAdmin)
admin.site.register(AttributeValue,AttributeValueAdmin)
admin.site.register(GroupHierarchy)
admin.site.register(GroupAttribute, GroupAttributeAdmin)
