import re
from pdb import set_trace

import django.utils.encoding
from django import forms
from django.conf import settings
from django.contrib import admin
from django.db.models import Case, F, IntegerField, Q, TextField, Value, When
from django.db.models.functions import Cast, Lower, StrIndex, Substr
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django_admin_multiple_choice_list_filter.list_filters import \
    MultipleChoiceListFilter
from rangefilter.filters import DateRangeFilter, DateTimeRangeFilter
from simple_history.admin import SimpleHistoryAdmin

from ordbok.forms import BegreppForm
from ordbok.models import *
from django.conf import settings

from ordbok import admin_actions
from ordbok.forms import BegreppExternalFilesForm, ChooseExportAttributes

admin.site.site_header = """OLLI Begreppstjänst Admin
 För fakta i livet"""
admin.site.site_title = "OLLI Begpreppstjänst Admin Portal"
admin.site.index_title = "Välkommen till OLLI Begreppstjänst Portalen"

def add_non_breaking_space_to_status(status_item):

    length = len(status_item)
    length_to_add = 12 - length
    for x in range(length_to_add):
        if x % 2 == 0:
            status_item += '&nbsp;'
        else:
            status_item = '&nbsp;' + status_item
    return mark_safe(status_item)

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

class BegreppExternalFilesInline(admin.StackedInline):

    model = BegreppExternalFiles
    extra = 1
    verbose_name = "Externt Kontext Fil"
    verbose_name_plural = "Externa Kontext Filer"

class ValideradAvDomänerInline(admin.StackedInline):
    
    model = Doman
    extra = 1
    verbose_name = "Validerad av"
    verbose_name_plural = "Validerad av"
    exclude = ['domän_kontext']

class StatusListFilter(MultipleChoiceListFilter):
    title = 'Status'
    template = "admin/multiple_status_filter.html"
    parameter_name = 'status__in'
    
    def lookups(self, request, model_admin):
        return STATUS_VAL

class BegreppAdmin(SimpleHistoryAdmin):

    class Media:
        css = {
        'all': (
            f'{settings.STATIC_URL}css/main.css',
            f'{settings.STATIC_URL}css/begrepp_custom.css',
           )
         }
    
    inlines = [BegreppExternalFilesInline, SynonymInline, ValideradAvDomänerInline]

    change_form_template = 'change_form_autocomplete.html'

    form = BegreppForm

    fieldsets = [
        ['Main', {
        'fields': [('datum_skapat','senaste_ändring'), ('status', 'id_vgr',)],
        }],
        [None, {
        #'classes': ['collapse'],
        'fields' : ['term',
                    'definition',
                    'link',
                    'källa',
                    'tidigare_definition_och_källa',
                    'anmärkningar',
                    'utländsk_term',
                    'term_i_system',
                    ('annan_ordlista', 'externt_id'),
                    ('begrepp_kontext'),
                    ('beställare','beställare__beställare_epost'),
                    'kommentar_handläggning']
        }]
    ]

    readonly_fields = ['senaste_ändring','datum_skapat','beställare__beställare_epost']
    history_list_display = ['changed_fields']

    def beställare__beställare_epost(self, obj):
        return obj.beställare.beställare_email

    save_on_top = True

    list_display = ('term',
                    'synonym',
                    'definition',
                    'status_button',
                    'senaste_ändring',)

    list_filter = (StatusListFilter,
                   ('senaste_ändring', DateRangeFilter),
    )

    search_fields = ('term',
                    'definition',
                    'utländsk_term',
                    'synonym__synonym',
                    )

    date_hierarchy = 'senaste_ändring'

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
            ).order_by('position').distinct()

            return queryset
        else:
            return queryset

    def position(self, obj):
        return obj.position
    position.short_description = 'Position'
    
    def has_link(self, obj):
        if (obj.link != None) and (obj.link != ''):
            return format_html(
            f'<img src="{settings.SUBDOMAIN}/static/admin/img/icon-yes.svg" alt="True">'
            )
        else:
            return format_html(
                f'<img src="{settings.SUBDOMAIN}/static/admin/img/icon-no.svg" alt="False">'
                )

    has_link.short_description = "URL Länk"

    def changed_fields(self, obj):
        if obj.prev_record:
            delta = obj.diff_against(obj.prev_record)
            return_text = ""
            for field in delta.changed_fields:
                # set_trace()
                return_text += f"""<p><strong>{field}</strong> ändrad från --> <span class="text_highlight_yellow">{getattr(delta.old_record, field)}</span></br></br>
                till --> <span class="text_highlight_green">{getattr(delta.new_record, field)}</span></p>"""
            return mark_safe(return_text)
        return None

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

    def export_chosen_begrepp_attrs_action(self, request, queryset):

        db_table_attrs = (field.name for field in queryset.first()._meta.get_fields() if field.name not in ['begrepp_fk', 
                                                                                                            'kommenterabegrepp',
                                                                                                            'begreppexternalfiles'])
        chosen_begrepp_ids = queryset.values_list('pk', flat=True)
        chosen_begrepp_terms = [i[0] for i in queryset.values_list('term')]

        
        return render(request, "choose_export_attrs_intermediate.html", context={"db_table_attrs" : db_table_attrs,
                                                                                 "chosen_begrepp" : chosen_begrepp_ids,
                                                                                 "chosen_begrepp_terms" : chosen_begrepp_terms})

    export_chosen_begrepp_attrs_action.short_description = "Exportera valde begrepp"

    actions = ['export_chosen_begrepp_attrs_action',]

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

    def get_domäner(self, obj):
        domäner = Doman.objects.filter(begrepp_id=obj.pk)
        return list(domäner)

    get_domäner.short_description = 'Validerad av'
    
    def status_button(self, obj):

        if (obj.status == 'Avråds') or (obj.status == 'Avrådd'):
            display_text = f'<button class="btn-xs btn-avrådd text-monospace">{add_non_breaking_space_to_status(obj.status)}</button>'
        elif (obj.status == 'Publicera ej'):
            display_text = f'<button class="btn-xs btn-light-blue text-monospace">{add_non_breaking_space_to_status(obj.status)}</button>'
        elif (obj.status == 'Pågår') or (obj.status == 'Ej Påbörjad'):
            display_text = f'<button class="btn-xs btn-oklart text-monospace">{add_non_breaking_space_to_status(obj.status)}</button>'
        elif (obj.status == 'Preliminär'):
            display_text = f'<button class="btn-xs btn-gul text-monospace">{add_non_breaking_space_to_status(obj.status)}</button>'
        elif (obj.status == 'Beslutad'):
            display_text = f'<button class="btn-xs btn-grön text-monospace">{add_non_breaking_space_to_status(obj.status)}</button>'
        else:
            display_text = f'<button class="btn-xs btn-white text-monospace">{add_non_breaking_space_to_status(obj.status)}</button>'
        return mark_safe(display_text)

    status_button.short_description = 'Status'

class BestallareAdmin(admin.ModelAdmin):

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
             for begrepp in obj.begrepp_set.all()
        ])
        if display_text:
            return mark_safe(display_text)
        return display_text

class DomanAdmin(admin.ModelAdmin):

    list_display = ('domän_namn',
                    'domän_id',
                    'domän_kontext',
                    'begrepp',)

    list_select_related = (
        'begrepp',
    )

    list_filter = ("domän_namn",)
    search_fields = ('begrepp__term',)

class SynonymAdmin(admin.ModelAdmin):

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "begrepp":
            kwargs["queryset"] = Begrepp.objects.filter().order_by(Lower('term'))
        return super(SynonymAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)

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


class KommenteraBegreppAdmin(admin.ModelAdmin):

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


class BegreppExternalFilesAdmin(admin.ModelAdmin):

    model = BegreppExternalFiles
    form = BegreppExternalFilesForm

    list_display = ('begrepp', 'kommentar', 'support_file')

admin.site.register(Begrepp, BegreppAdmin)
admin.site.register(Bestallare, BestallareAdmin)
admin.site.register(Doman, DomanAdmin)
admin.site.register(Synonym, SynonymAdmin)
admin.site.register(KommenteraBegrepp, KommenteraBegreppAdmin)
admin.site.register(SökFörklaring, SökFörklaringAdmin)
admin.site.register(SökData, SökDataAdmin)
admin.site.register(BegreppExternalFiles,BegreppExternalFilesAdmin)
