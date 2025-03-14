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
                                     export_chosen_concepts_action)

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
                   f'{settings.STATIC_URL}css/admin_kommentarmodel_custom.css'
            )
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
                set_trace()
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
        set_trace()
        if db_field.name == "kommentar":
            # Filter the queryset for the ForeignKey field based on the user's group
            user_groups = request.user.groups.all()
            kwargs["queryset"] = ConceptComment.objects.filter(
            concept__concept_fk__groups__in=user_groups
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

    def get_fields(self, request, obj=None):
        """
        Retrieves the fields dynamically and sorts them based on GroupAttribute.position.
        """
        if not obj:
            return ["attribute"]  # Default when no instance is selected

        # Get the term's groups (or another relevant relation)
        term_groups = obj.dictionaries.values_list("groups", flat=True)
        # attributes = Attribute.objects.filter(groups__id__in=term_groups).distinct()

        # term_groups = obj.dictionaries.all()  # Adjust this if needed
        attributes = Attribute.objects.filter(groups__in=term_groups).distinct()

        # Get sorted attributes based on GroupAttribute position
        group_attributes = GroupAttribute.objects.filter(attribute__in=attributes).order_by("position")

        # Extract the sorted attributes
        sorted_attributes = [ga.attribute for ga in group_attributes]

        # Field mapping for each attribute type
        field_map = {
            'string': 'value_string',
            'text': 'value_text',
            'integer': 'value_integer',
            'decimal': 'value_decimal',
            'boolean': 'value_boolean',
            'url': 'value_url'
        }

        # Get the ordered fields (ensuring only one value field per attribute)
        sorted_fields = ["attribute"] + [
            field_map[attr.data_type] for attr in sorted_attributes if attr.data_type in field_map
        ]
        return sorted_fields
    

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

    list_display = ['term', 'definition', 'status_button', 'changed_at', 'list_dictionaries']
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

    list_dictionaries.short_description = 'Ordbok'
    list_dictionaries.verbose_name_plural = 'Ordböcker'
    list_dictionaries.verbose_name = 'Ordbok'

    def export_chosen_attrs_view(request):

        # Required default fields
        default_fields = ["Id", "Term", "Definition", "Status"]

        if request.method == 'GET':   
            chosen_concepts = [int(i) for i in request.GET.get('selected_concepts').split("&")]
            logger.debug(f"Exporting the following - {chosen_concepts}")
            queryset = Concept.objects.filter(id__in=chosen_concepts)
        # Step 1: Create a mapping from verbose_name to actual field names
        field_mapping = {
            field.verbose_name: field.name
            for field in queryset.first()._meta.get_fields()
            if hasattr(field, "verbose_name") and field.verbose_name
        }

        # Step 2: Get user-selected attributes from request
        selected_attributes_verbose = request.GET.getlist("attributes")  # User selects verbose_name

        # Separate the default fields from the rest
        other_fields = sorted([f for f in selected_attributes_verbose if f not in default_fields], key=str.lower)

        # Combine: First four in order, rest alphabetically
        sorted_fields = default_fields + other_fields
        # selected_attributes = [field_mapping.get(attr, attr) for attr in selected_attributes_verbose]
        
        form = ChooseExportAttributes(request.GET)
        if form.is_valid():
            response = admin_actions.export_chosen_concept_as_csv(request=request, queryset=queryset, selected_fields=sorted_fields, field_mapping=field_mapping)
        return response
    
    export_chosen_concepts_action.short_description = "Exportera valde begrepp"    
    actions = [export_chosen_concepts_action,]

class AttributeAdmin(admin.ModelAdmin):

    list_display = ['display_name', 'data_type', 'description', 'list_groups']

    def list_groups(self, obj):
        return ", ".join([group.name for group in obj.groups.all()])

class AttributeValueAdmin(admin.ModelAdmin):

    model = AttributeValue

    list_display = ['term', 'attribute__display_name', 'get_value']

    search_fields = [
    'term__id',
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
