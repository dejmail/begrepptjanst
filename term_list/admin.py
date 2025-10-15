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
from django.utils.translation import gettext_lazy as _


from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.contrib.admin.filters import RelatedFieldListFilter

from django_admin_multiple_choice_list_filter.list_filters import (
    MultipleChoiceListFilter
)
from django.core.exceptions import PermissionDenied

from django.contrib import messages


from rangefilter.filters import DateRangeFilterBuilder
from simple_history.admin import SimpleHistoryAdmin
from django.http import HttpResponseRedirect

from term_list.forms import (
    ConceptForm, 
    AttributeValueInlineForm,
    ConfigurationOptionsForm
    # AttributeValueInlineFormSet
    )
from term_list.models import *
from django.conf import settings

from term_list import admin_actions
from term_list.forms import ConceptExternalFilesForm, ChooseExportAttributes
from term_list.admin_actions import (
    change_dictionaries, 
    export_chosen_concepts_action,
    delete_allowed_objects
)
from django.contrib.admin.actions import delete_selected


from django.core.files.uploadedfile import InMemoryUploadedFile

admin.site.site_header = """OLLI Begreppstjänst Admin - 
 För fakta i livet"""
admin.site.site_title = "OLLI Begpreppstjänst Admin Portal"
admin.site.index_title = "Välkommen till OLLI Begreppstjänst Portalen"

from term_list.admin_functions import (
    DictionaryRestrictedAdminMixin,
    DictionaryRestrictedInlineMixin,
    ConceptFileImportMixin,
    DictionaryFilter,
    DuplicateTermFilter,
    add_non_breaking_space_to_status
    )

logger = logging.getLogger(__name__)

class SynonymInlineForm(forms.ModelForm):

    class Meta:
        model = Synonym
        fields = "__all__"
        labels = {"synonym": "Synonym"}


    def clean(self):
        super(SynonymInlineForm, self).clean()
        if self.cleaned_data.get('synonym') == None:
            self.add_error('synonym', 'Kan inte radera synonym med bak knappen, använder checkbox till höger')

class SynonymInline(admin.TabularInline):

    model = Synonym
    form = SynonymInlineForm
    extra = 1
    min_num = 0
    verbose_name = "Synonym"
    verbose_name_plural = "Synonymer"


    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        formset.form.user = request.user  # Pass the user to the form
        parent = kwargs.pop('parent_model_admin', None)
        if parent is not None:
            self.parent_model_admin = parent
        return super().get_formset(request, obj, **kwargs)
        # return formset

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

class TaskOrdererAdmin(
    admin.ModelAdmin):

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

class DictionaryAdmin(
    admin.ModelAdmin):

    list_display = ('dictionary_name',
                    'dictionary_id',
                    'dictionary_context',
                    'order')

    list_filter = ("dictionary_name",)
    #search_fields = ('begrepp__term',)

    def _get_dictionary_from_obj(self,  request, obj):
        print("✅ DictionaryAdmin._get_dictionary_from_obj called")
        return Dictionary.objects.filter(pk=obj.pk)


class SynonymAdmin(
    admin.ModelAdmin):
    
    ordering = ['concept__term']
    list_display = ('concept',
                    'synonym',
                    'synonym_status',
                    'get_dictionaries',)

    list_select_related = (
        'concept',
    )
    list_filter = ("synonym_status", DictionaryFilter)
    search_fields = ("concept__term", "synonym")

    def _get_dictionary_from_obj(self, request, obj):
        return obj.concept.dictionaries.all() if obj and obj.concept else Dictionary.objects.none()

    def get_actions(self, request):
        actions = super().get_actions(request)
        return actions

    def get_actions(self, request):
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions
    
    @admin.action(description="Radera valda synonymer")
    def delete_synonyms(modeladmin, request, queryset):

        return delete_allowed_objects(
            modeladmin,
            request,
            queryset,
            object_label="synonymer",
            permission_check=modeladmin._user_has_dictionary_access
        )
    
    actions = [delete_synonyms]
  

    def has_delete_permission(self, request, obj=None):
        return True

    def get_dictionaries(self, obj):
        # Assuming term has a many-to-many relationship to dictionaries
        
        return ", ".join(d.dictionary_long_name for d in obj.concept.dictionaries.all())
    get_dictionaries.short_description = "Ordböcker"


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


class ConceptCommentsAdmin(
    # DictionaryRestrictedAdminMixin, 
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

class ConceptExternalFilesAdmin(
    # DictionaryRestrictedAdminMixin, 
    admin.ModelAdmin):

    model = ConceptExternalFiles
    form = ConceptExternalFilesForm

    list_display = ('concept', 'comment', 'support_file')

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "kommentar":
            # Filter the queryset for the ForeignKey field based on the user's group
            user_groups = request.user.groups.all()
            kwargs["queryset"] = ConceptComment.objects.filter(
            concept__concept_fk__groups__in=user_groups
            ).distinct()

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

class ConfigurationOptionsAdmin(admin.ModelAdmin):
    
    model = ConfigurationOptions
    form = ConfigurationOptionsForm

    list_display = ['name', 'description', 'pretty_json']

    def pretty_json(self, obj):
        # value = json.loads(obj.config)
        pretty = json.dumps(obj.config, indent=2, ensure_ascii=False)
        # pretty = json.dumps(obj.config, indent=2, ensure_ascii=False)
        # Wrap in <pre> for formatting
        return mark_safe(f'<pre>{pretty}</pre>')
    pretty_json.short_description = "Config"

class AttributeValueInline(
    DictionaryRestrictedInlineMixin, 
    admin.StackedInline
    ):
    model = AttributeValue
    form = AttributeValueInlineForm
    fk_name = "term"
    extra = 0
    can_delete = False
    # template = "admin/edit_inline/stacked.html" 

    def get_parent_object(self, request):
        return getattr(request, '_admin_form_parent_instance', None)

    # def get_formset(self, request, obj=None, **kwargs):
    #     self.parent_model_admin = self.admin_site._registry.get(obj.__class__)
    #     return super().get_formset(request, obj, **kwargs)

    def get_formset(self, request, obj=None, **kwargs):
        """
        Force-disable all form fields when the parent object isn't changeable.
        This works regardless of templates or custom widgets.
        """
        # Ensure the inline knows its parent admin (ConceptAdmin)
        if obj is not None and not getattr(self, "parent_model_admin", None):
            self.parent_model_admin = self.admin_site._registry.get(obj.__class__)

        # If we cannot change the Concept, disable all inline fields
        can_change = self.has_change_permission(request, obj=obj)

        if not can_change:
            self.readonly_fields = tuple(self.get_fields(request, obj))
            self.can_delete = False
            self.max_num = 0
            kwargs.setdefault("extra", 0)
        else:
            self.readonly_fields = getattr(self, "readonly_fields", ())

        FormSet = super().get_formset(request, obj, **kwargs)

        if not can_change:
            FormSet.can_delete = False
            orig_init = FormSet.form.__init__
            def disabled_init(formself, *a, **k):
                orig_init(formself, *a, **k)
                for f in formself.fields.values():
                    f.disabled = True
            FormSet.form.__init__ = disabled_init

        return FormSet


    def has_add_permission(self, request, obj=None):
        return False  # ✅ Prevents the 'Add another' button from appearing

    def has_change_permission(self, request, obj=None):
        if obj is None:
            return True  # early calls during construction
        p = getattr(self, "parent_model_admin", None)
        if p is not None:
            return p.has_change_permission(request, obj=obj)
        return self._has_permission(request, obj)

        return p.has_change_permission(request, obj=obj)

    # ✅ Make the inline read-only if parent says “no change” on this Concept
    def get_readonly_fields(self, request, obj=None):
        if obj and not self.has_change_permission(request, obj):
            return tuple(self.get_fields(request, obj))
        return super().get_readonly_fields(request, obj)

    # ✅ Hide “add another” row when read-only (belt & braces)
    def get_max_num(self, request, obj=None, **kwargs):
        if obj and not self.has_change_permission(request, obj):
            return 0
        return super().get_max_num(request, obj, **kwargs)

    def get_fields(self, request, obj=None):
        """
        Retrieves the fields dynamically and sorts them based on GroupAttribute.position.
        """
        if not obj:
            return ["attribute"]  # Default when no instance is selected

        # Get the term's groups (or another relevant relation)
        term_groups = obj.dictionaries.values_list("groups", flat=True)

        attributes = Attribute.objects.filter(groups__in=term_groups).distinct()

        # Get sorted attributes based on GroupAttribute position
        group_attributes = GroupAttribute.objects.filter(attribute__in=attributes).order_by("position")

        sorted_attributes = [ga.attribute for ga in group_attributes]

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

class AllDictionaryFilter(RelatedFieldListFilter):

    def __init__(self, field, request, params, model, model_admin, field_path):
        super().__init__(field, request, params, model, model_admin, field_path)
        self.title = _("Dictionaries")


    def field_choices(self, field, request, model_admin):
        from .models import Dictionary
        qs = Dictionary.objects.all().order_by("dictionary_name")
        return [(d.pk, str(d)) for d in qs]

class ConceptAdmin(DictionaryRestrictedAdminMixin,
                   ConceptFileImportMixin,
                   SimpleHistoryAdmin,
                   admin.ModelAdmin):

    model = Concept
    form = ConceptForm

    class Media:
        css = {
        'all': (
            f'{settings.STATIC_URL}css/main.css',
            f'{settings.STATIC_URL}css/begrepp_custom.css',
           )
         }
        
    change_form_template = 'begrepp_change_form.html'
    change_list_template = "begrepp_changelist.html"

    list_display = ['term', 'definition', 'status_button', 'changed_at', 'list_dictionaries']
    search_fields = ('term',
                    'definition',
                    'synonyms__synonym',
                    )
    
    list_filter = (StatusListFilter,
                   ('changed_at', DateRangeFilterBuilder()),
                   ("dictionaries", AllDictionaryFilter),
                   DuplicateTermFilter
    )

    # --- defaults for the first page load ---
    DICT_PARAM = "dictionaries__dictionary_id__exact"
    DEFAULT_SUPERUSER_DICT_NAME = "VGR gemensam"
    
    inlines = [AttributeValueInline, SynonymInline]

    def _default_dictionary_id(self, request):
        """Pick the default dictionary id for this user."""
        if request.user.is_superuser:
            return (
                Dictionary.objects
                .filter(dictionary_name=self.DEFAULT_SUPERUSER_DICT_NAME)
                .values_list("dictionary_id", flat=True)
                .first()
            )
        # Limited users: start on one of the dictionaries they can access
        qs = self.get_accessible_dictionaries(request)
        return qs.order_by("dictionary_name").values_list("dictionary_id", flat=True).first()

    def changelist_view(self, request, extra_context=None):
        """
        If no dictionary filter is present, redirect to the same URL
        with a default 'dictionaries__id__exact=<id>' applied.
        """
        if request.method == "GET" and self.DICT_PARAM not in request.GET:
            default_id = self._default_dictionary_id(request)
            if default_id:
                params = request.GET.copy()
                params[self.DICT_PARAM] = str(default_id)
                return HttpResponseRedirect(f"{request.path}?{params.urlencode()}")
        return super().changelist_view(request, extra_context)
    
    def has_view_permission(self, request, obj=None):
        # Let any authenticated staff view terms (even outside their dictionaries).
        return request.user.is_active and request.user.is_staff

    def get_readonly_fields(self, request, obj=None):
        # If user lacks change permission on this object, make the form read-only.
        ro = list(super().get_readonly_fields(request, obj))
        if obj and not self.has_change_permission(request, obj=obj):
            # All concrete fields read-only
            ro = sorted(set(ro + [f.name for f in self.model._meta.fields]))
        return ro

    def _get_dictionary_from_obj(self, request, obj):
        return obj.dictionaries.all() if obj else Dictionary.objects.none()
    

    def _get_dictionary_lookup(self):
        return 'dictionaries__in'
    
    @admin.action(description="Radera valda begrepp")
    def delete_concepts(modeladmin, request, queryset):
        return delete_allowed_objects(
            modeladmin,
            request,
            queryset,
            object_label="begrepp",
        )
    
    def get_actions(self, request):
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

    def get_inline_instances(self, request, obj=None):

        if obj is None:
            return []
        instances = super().get_inline_instances(request, obj)
        for inline in instances:
            inline.parent_model_admin = self
        return instances
    
    def status_button(self, obj):
        status_classes = {
        'Avråds': 'tag tag-red text-monospace',
        'Avrådd': 'tag tag-red text-monospace',
        'Avställd': 'tag tag-red text-monospace',
        'Publicera ej': 'tag tag-light-blue text-monospace dark-text',
        'Pågår': 'tag tag-orange light-text text-monospace',
        'Ej Påbörjad': 'tag tag-orange dark-text text-monospace',
        'Beslutad': 'tag tag-green light-text text-monospace'
        }

        css_class = status_classes.get(obj.status, 'tag btn-white dark-text text-monospace')
        
        display_text = f'<span class="{css_class}">{add_non_breaking_space_to_status(obj.status)}</span>'
        return mark_safe(display_text)

    status_button.short_description = 'Status'
    
    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        concept = self.get_object(request, object_id)
        
        if concept:
            # Filter attributes based on the Concept's dictionary
            
            extra_context['filtered_attributes'] = Attribute.objects.filter(
            groups__dictionaries__in=concept.dictionaries.all()
            )
        
        return super().change_view(request, object_id, form_url, extra_context=extra_context)


    def get_form(self, request, obj=None, **kwargs):
        form_class = super().get_form(request, obj, **kwargs)

        class FormWithUser(form_class):
            def __init__(self2, *args, **kwargs2):
                logger.info(f"Injecting user: {request.user}")
                kwargs2['user'] = request.user
                super().__init__(*args, **kwargs2)

        return FormWithUser

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

        # # Now that ManyToMany relationships are saved, proceed with AttributeValues
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
    actions = [export_chosen_concepts_action, delete_concepts]

class AttributeAdmin(admin.ModelAdmin):

    list_display = ['display_name', 'data_type', 'description', 'list_groups']

    # def _get_dictionary_from_obj(self, obj):
    #     return obj.term.dictionaries.first()

    # def _get_dictionary_lookup(self):
    #     return 'term__dictionaries__in'

    def list_groups(self, obj):
        return ", ".join([group.name for group in obj.groups.all()])

class AttributeValueAdmin(
    #  DictionaryRestrictedAdminMixin, 
    admin.ModelAdmin):

    model = AttributeValue
    actions = [delete_selected]

    list_display = ['term', 'attribute__display_name', 'get_value', 'term__dictionaries__dictionary_long_name']

    search_fields = [
    'term__id',
    'term__term',
    'attribute__display_name',
    'value_string',
    'value_text',
    'value_integer',
    'value_decimal',
    'value_boolean',
    'value_url'
    ]

    def _get_dictionary_from_obj(self, request, obj):
        return obj.term.dictionaries.first()

    def _get_dictionary_lookup(self):
        return 'term__dictionaries__in'
    
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
admin.site.register(GroupHierarchy)
admin.site.register(GroupAttribute, GroupAttributeAdmin)
