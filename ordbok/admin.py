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

from ordbok.forms import BegreppForm, ColumnMappingForm, ExcelImportForm
from ordbok.models import *
from django.conf import settings

from ordbok import admin_actions
from ordbok.forms import BegreppExternalFilesForm, ChooseExportAttributes
from ordbok.admin_actions import (change_dictionaries,
                                  export_chosen_begrepp_attrs_action)

from django.core.files.uploadedfile import InMemoryUploadedFile

admin.site.site_header = """OLLI Begreppstjänst Admin
 För fakta i livet"""
admin.site.site_title = "OLLI Begpreppstjänst Admin Portal"
admin.site.index_title = "Välkommen till OLLI Begreppstjänst Portalen"

from ordbok.admin_functions import (DictionaryRestrictAdminMixin,
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

class BegreppExternalFilesInline(admin.StackedInline):

    model = BegreppExternalFiles
    extra = 1
    verbose_name = "Externt Kontext Fil"
    verbose_name_plural = "Externa Kontext Filer"

class StatusListFilter(MultipleChoiceListFilter):
    title = 'Status'
    template = "admin/multiple_status_filter.html"
    parameter_name = 'status__in'
    
    def lookups(self, request, model_admin):
        return STATUS_VAL

class ExcelImportForm(forms.Form):
    excel_file = forms.FileField()

class BegreppAdmin(DictionaryRestrictAdminMixin,
                   ConceptFileImportMixin,
                   SimpleHistoryAdmin):

    class Media:
        css = {
        'all': (
            f'{settings.STATIC_URL}css/main.css',
            f'{settings.STATIC_URL}css/begrepp_custom.css',
           )
         }
    
    inlines = [BegreppExternalFilesInline, SynonymInline]

    change_form_template = 'begrepp_change_form.html'
    change_list_template = "begrepp_changelist.html"

    form = BegreppForm

    readonly_fields = ['senaste_ändring','datum_skapat']
    history_list_display = ['changed_fields']

    save_on_top = True

    list_display = ('term',
                    'synonym',
                    'definition',
                    'status_button',
                    'senaste_ändring',
                    'list_dictionaries')

    list_filter = (StatusListFilter,
                   ('senaste_ändring', DateRangeFilter),
                   DictionaryFilter,
                   DuplicateTermFilter
    )

    filter_horizontal = ('dictionaries',)

    search_fields = ('term',
                    'definition',
                    'utländsk_term',
                    'synonym__synonym',
                    )

    date_hierarchy = 'senaste_ändring'

    actions = [change_dictionaries, export_chosen_begrepp_attrs_action]

    def get_queryset(self, request):

        queryset = super().get_queryset(request)
        
        if request.GET.get('q'):
            search_term = request.GET.get('q')
            queryset = queryset.annotate(
                position=Case(
                    When(Q(term__iexact=search_term), then=Value(1)),
                    When(Q(term__istartswith=search_term), then=Value(2)),
                    When(Q(term__icontains=search_term), then=Value(3)), 
                    When(Q(synonym__synonym__icontains=search_term), then=Value(4)), 
                    When(Q(utländsk_term__icontains=search_term), then=Value(5)),
                    When(Q(definition__icontains=search_term), then=Value(6)), 
                    default=Value(0),
                    output_field=IntegerField()
                )
            ).order_by('position')
        if not request.user.is_superuser:
            accessible_dictionaries = self.get_accessible_dictionaries(request)
            return queryset.filter(dictionaries__in=accessible_dictionaries).distinct()
        else:
            return queryset
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
                
        # Only show dictionaries the user has permission to edit
        if not request.user.is_superuser:
            
            # Assuming you have a relation like 'dictionary' in Begrepp model
            form.base_fields['dictionaries'].queryset = form.base_fields['dictionaries'].queryset.filter(
                groups__in=request.user.groups.all()
            )

        return form
    
    # def changelist_view(self, request, extra_context=None):
    #     extra_context = extra_context or {}
    #     extra_context['available_dictionaries'] = Dictionary.objects.all()
    #     return super(BegreppAdmin, self).changelist_view(request, extra_context=extra_context)
    
    def get_fieldsets(self, request, obj=None):
        # Get visible config in the required order
        config = ConfigurationOptions.objects.get(name='visibleOnFrontPage').config

        # Combine regular fields and ManyToManyFields
        all_fields = list(self.model._meta.fields) + list(self.model._meta.many_to_many)

        # Initialize dictionaries to hold the ordered fields
        visible_fields = []
        other_fields = []

        # Loop through the config to ensure the correct order of visible fields
        for field_name in config:
            if any(field.name == field_name for field in all_fields):
                visible_fields.append(field_name)

        # Add remaining fields to 'other_fields' in any order
        for field in all_fields:
            if field.name != 'id' and field.name not in visible_fields:
                other_fields.append(field.name)

            # Define the fieldsets based on the lists of fields
        fieldsets = (
            ('Synliga attribut på framsida', {'fields': visible_fields}),
            ('Övriga attribut', {'fields': other_fields}),
        )
        return fieldsets

    
    def position(self, obj):
        return obj.position
    position.short_description = 'Position'
    
    def has_link(self, obj):
        if (obj.link != None) and (obj.link != ''):
            return format_html(
            f'<img src="{settings.SUBDOMAIN}/static/admin/img/icon-yes.svg" alt="Har länk ikon">'
            )
        else:
            return format_html(
                f'<img src="{settings.SUBDOMAIN}/static/admin/img/icon-no.svg" alt="Har ingen länk ikon">'
                )

    has_link.short_description = "URL Länk"

    def changed_fields(self, obj):
        if obj.prev_record:
            delta = obj.diff_against(obj.prev_record)
            return_text = ""
            for field in delta.changed_fields:
                return_text += f"""<p><strong>{field}</strong> ändrad från --> <span class="text_highlight_yellow">{getattr(delta.old_record, field)}</span></br></br>
                till --> <span class="text_highlight_green">{getattr(delta.new_record, field)}</span></p>"""
            return mark_safe(return_text)
        return None
    
    def get_actions(self, request):
        actions = super().get_actions(request)
        actions['change_dictionaries'] = (change_dictionaries, 'change_dictionaries', "Change Dictionary of selected Begrepp")
        return actions

  

    def export_chosen_attrs_view(request):

        if request.method == 'POST':
            chosen_begrepp = [int(i) for i in request.POST.get('selected_begrepp').split("&")[:-1]]
            queryset = Begrepp.objects.filter(id__in=chosen_begrepp)
            model_fields = [field.name for field in queryset.first()._meta.get_fields()]
            chosen_table_attrs = [i for i in model_fields if i in request.POST.keys()]

            form = ChooseExportAttributes(request.POST)
            if form.is_valid():
                response = admin_actions.export_chosen_begrepp_as_csv(request=request, queryset=queryset, field_names=chosen_table_attrs)
            return response

    def önskad_slutdatum(self, obj):
        
        return obj.beställare.önskad_slutdatum

    def synonym(self, obj):
        
        display_text = ", ".join([
            "<a href={}>{}</a>".format(
                    reverse('admin:{}_{}_change'.format(obj._meta.app_label,  obj._meta.related_objects[2].name),
                    args=(synonym.id,)),
                synonym.synonym)
             for synonym in obj.synonym_set.all()
        ])
        if display_text:
            return mark_safe(display_text)
        return "-"

    synonym.admin_order_field = 'synonym'

    def list_dictionaries(self, obj):
        return ", ".join([dictionary.dictionary_name for dictionary in obj.dictionaries.all()])

    list_dictionaries.short_description = 'Ordbok'
    list_dictionaries.verbose = 'Ordböcker'
    
    
    def status_button(self, obj):

        if (obj.status == 'Avråds') or (obj.status == 'Avrådd'):
            display_text = f'<span class="tag tag-avrådd text-monospace">{add_non_breaking_space_to_status(obj.status)}</span>'
        elif (obj.status == 'Publicera ej'):
            display_text = f'<span class="tag tag-light-blue text-monospace">{add_non_breaking_space_to_status(obj.status)}</span>'
        elif (obj.status == 'Pågår') or (obj.status == 'Ej Påbörjad'):
            display_text = f'<span class="tag tag-oklart text-monospace">{add_non_breaking_space_to_status(obj.status)}</span>'
        elif (obj.status == 'Preliminär'):
            display_text = f'<span class="btn-xs btn-gul text-monospace">{add_non_breaking_space_to_status(obj.status)}</span>'
        elif (obj.status == 'Beslutad'):
            display_text = f'<span class="tag tag-grön text-monospace">{add_non_breaking_space_to_status(obj.status)}</span>'
        else:
            display_text = f'<span class="tag btn-white text-monospace">{add_non_breaking_space_to_status(obj.status)}</span>'
        return mark_safe(display_text)

    status_button.short_description = 'Status'

class BestallareAdmin(DictionaryRestrictAdminMixin, admin.ModelAdmin):

    list_display = ('beställare_namn',
                    'beställare_email',
                    'beställare_telefon',
                    'beställare_datum',
                    'önskad_slutdatum',
                    'begrepp')
    search_fields = ("begrepp__term","beställare_namn", "beställare_email") 

    def begrepp(self, obj):
        
        display_text = ", ".join([
            "<a href={}>{}</a>".format(
                    reverse('admin:{}_{}_change'.format(obj._meta.app_label,  obj._meta.related_objects[0].name),
                    args=(begrepp.id,)),
                begrepp.term)
             for begrepp in obj.begrepp.all()
        ])
        if display_text:
            return mark_safe(display_text)
        return display_text

class DictionaryAdmin(DictionaryRestrictAdminMixin, admin.ModelAdmin):

    list_display = ('dictionary_name',
                    'dictionary_id',
                    'dictionary_context',
                    'order')

    #list_select_related = (
    #    'begrepp',
    #)

    list_filter = ("dictionary_name",)
    #search_fields = ('begrepp__term',)

class SynonymAdmin(DictionaryRestrictedOtherModelAdminMixin, admin.ModelAdmin):
    
    ordering = ['begrepp__term']
    list_display = ('begrepp',
                    'synonym',
                    'synonym_status')

    list_select_related = (
        'begrepp',
    )
    list_filter = ("synonym_status",)
    search_fields = ("begrepp__term", "synonym")

class ContextFilesInline(admin.StackedInline):

    model = BegreppExternalFiles
    extra = 1
    verbose_name = "Externt Kontext Fil"
    verbose_name_plural = "Externa Kontext Filer"
    exclude = ('begrepp',)


class KommenteraBegreppAdmin(DictionaryRestrictedOtherModelAdminMixin, 
                             admin.ModelAdmin):

    class Media:
        css = {

            'all': ('https://use.fontawesome.com/releases/v5.8.2/css/all.css',
                   f'{settings.STATIC_URL}css/admin_kommentarmodel_custom.css',
                   f'{settings.STATIC_URL}css/custom_icon.css')
            }

    inlines = [ContextFilesInline,]

    list_display = ('begrepp',
                    'begrepp_kontext',
                    'bifogade_filer',
                    'datum',
                    'epost',
                    'namn',
                    'status',
                    'telefon',
                    )

    list_filter = ('status',)

    readonly_fields = ['datum',]

    fieldsets = [
        ['Main', {
        'fields': [('begrepp', 'datum'), 
        ('begrepp_kontext',), 
        ('epost','namn','status','telefon'),]},
        ]]

    def bifogade_filer(self, obj):

        if (obj.begreppexternalfiles_set.exists()) and (obj.begreppexternalfiles_set.name != ''):
            return format_html(f'''<a href={obj.begreppexternalfiles_set}>
                                    <i class="fas fa-file-download">
                                    </i>
                                    </a>''')
        else:
            return format_html(f'''<span style="color: red;">            
                                       <i class="far fa-times-circle"></i>
                                    </span>''')
    bifogade_filer.short_description = "Bifogade filer"

    def save_formset(self, request, form, formset, change):
        
        if request.method == 'POST':
            instances = formset.save(commit=False)
            for instance in instances:
                if not instance.begrepp_id:
                    instance.begrepp_id = form.cleaned_data.get('begrepp').pk
                instance.save()
        formset.save_m2m()

class SökFörklaringAdmin(admin.ModelAdmin):

    list_display = ('sök_term',
                    'ip_adress',
                    'sök_timestamp')

class SökDataAdmin(admin.ModelAdmin):

    list_display = ('sök_term',
                    'ip_adress',
                    'sök_timestamp',
                    'records_returned')

class BegreppExternalFilesAdmin(DictionaryRestrictedOtherModelAdminMixin, 
                                admin.ModelAdmin):

    model = BegreppExternalFiles
    form = BegreppExternalFilesForm

    list_display = ('begrepp', 'kommentar', 'support_file')

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "kommentar":
            # Filter the queryset for the ForeignKey field based on the user's group
            user_groups = request.user.groups.all()
            kwargs["queryset"] = KommenteraBegrepp.objects.filter(
            begrepp__begrepp_fk__groups__in=user_groups
            ).distinct()

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

class ConfigurationOptionsAdmin(admin.ModelAdmin):
    
    model = ConfigurationOptions

admin.site.register(Begrepp, BegreppAdmin)
admin.site.register(Bestallare, BestallareAdmin)
admin.site.register(Dictionary, DictionaryAdmin)
admin.site.register(Synonym, SynonymAdmin)
admin.site.register(KommenteraBegrepp, KommenteraBegreppAdmin)
admin.site.register(SökFörklaring, SökFörklaringAdmin)
admin.site.register(SökData, SökDataAdmin)
admin.site.register(BegreppExternalFiles,BegreppExternalFilesAdmin)
admin.site.register(ConfigurationOptions, ConfigurationOptionsAdmin)

