from pdb import set_trace
from django.urls import reverse
from django.db.models.functions import Lower
from django.utils.safestring import mark_safe
from django.conf import settings
from django.utils.html import format_html
import django.utils.encoding

from django.contrib import admin
from ordbok.models import Begrepp, Bestallare, Doman, OpponeraBegreppDefinition, Synonym, SökData, SökFörklaring
from .functions import skicka_epost_till_beställaren

import re

admin.site.site_header = "OLLI Begreppstjänst Admin"
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

class SynonymInline(admin.StackedInline):
    model = Synonym
    extra = 1

class BegreppAdmin(admin.ModelAdmin):
    
    class Media:
        css = {
        'all': (f'{settings.STATIC_URL}css/main.css',)
         }
    
    inlines = [SynonymInline]

    fieldsets = [
        ['Main', {
        'fields': ['begrepp_version_nummer', ('status', 'id_vgr',)],
        }],
        [None, {
        #'classes': ['collapse'],
        'fields' : [#'synonym',
                    'term',
                    'definition',
                    'källa',
                    'alternativ_definition',
                    'anmärkningar',
                    'utländsk_term',
                    'utländsk_definition',
                    ('annan_ordlista', 'externt_id'),
                    'begrepp_kontext',
                    'beställare',
                    #'domän',
                    'kommentar_handläggning']
        }]
    ]

    readonly_fields = ('begrepp_version_nummer',)

    save_on_top = True

    list_display = ('term',
                    'synonym',
                    'definition',
                    'utländsk_term',
                    'utländsk_definition',
                    'status_button',
                    #'visa_html_i_begrepp_kontext',    
                    'annan_ordlista',
                    'begrepp_version_nummer',
                    'beställare')

    list_filter = ("begrepp_version_nummer", "status",)

    search_fields = ('term',
                    'definition',
                    'begrepp_kontext',    
                    'annan_ordlista',
                    'term',
                    'utländsk_definition',
                    'utländsk_term',
                    'begrepp_version_nummer',
                    'status')

    date_hierarchy = 'begrepp_version_nummer'

    actions = ['skicka_epost_till_beställaren',]

    def skicka_epost_till_beställaren(self, request, queryset):

        skicka_epost_till_beställaren(queryset)

    skicka_epost_till_beställaren.short_description = "Skicka epost till beställaren"

    def synonym(self, obj):
        display_text = ", ".join([
            "<a href={}>{}</a>".format(
                    reverse('admin:{}_{}_change'.format(obj._meta.app_label,  obj._meta.related_objects[1].name),
                    args=(synonym.id,)),
                synonym.synonym)
             for synonym in obj.synonym_set.all()
        ])
        if display_text:
            return mark_safe(display_text)
        return "-"

    # def visa_html_i_begrepp_kontext(self, obj):
        
    #     set_trace()
    #     if len(re.findall("|") > 1:
    #     if ("|" in obj.begrepp_kontext) and ('http' in obj.begrepp_kontext):
    #         set_trace()
    #         description, url = obj.begrepp_kontext.split('|')

    #         display_text = f"<a href={url}>{description}</a>"
    #         return mark_safe(display_text)
    #     else:
    #     return obj.begrepp_kontext

    # visa_html_i_begrepp_kontext.short_description = "begrepp context"
    
    def status_button(self, obj):

        if (obj.status == 'Avråds') or (obj.status == 'Avrådd'):
            display_text = f'<button class="btn-xs btn-avrådd text-monospace">{add_non_breaking_space_to_status(obj.status)}</button>'
        elif (obj.status == 'Publicera ej'):
            display_text = f'<button class="btn-xs btn-light-blue text-monospace">{add_non_breaking_space_to_status(obj.status)}</button>'
        elif (obj.status == 'Pågår') or (obj.status == 'Ej Påbörjad'):
            display_text = f'<button class="btn-xs btn-oklart text-monospace">{add_non_breaking_space_to_status(obj.status)}</button>'
        elif (obj.status == 'Preliminär'):
            display_text = f'<button class="btn-xs btn-gul text-monospace">{add_non_breaking_space_to_status(obj.status)}</button>'
        else:
            display_text = f'<button class="btn-xs btn-grön text-monospace">{add_non_breaking_space_to_status(obj.status)}</button>'
        return mark_safe(display_text)

    status_button.short_description = 'Status'

    # def save_model(self, request, obj, form, change):
    #     if "http" in obj.begrepp_kontext:
    #         obj.begrepp_kontext = f"<a href={obj.begrepp_kontext}>SCT{obj.begrepp_kontext.split('/')[-1]}</a>"           
    #     super().save_model(request, obj, form, change)

class BestallareAdmin(admin.ModelAdmin):

    list_display = ('beställare_namn',
                    'beställare_email',
                    'beställare_telefon',
                    'beställare_datum',
                    'begrepp')
    search_fields = ("begrepp__term","beställare_namn", "beställare_email") 

    def begrepp(self, obj):
        # set_trace()
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

class OpponeraBegreppDefinitionAdmin(admin.ModelAdmin):

    list_display = ('begrepp',
                    'begrepp_kontext',
                    'datum',
                    'epost',
                    'namn',
                    'status',
                    'telefon')

class SökFörklaringAdmin(admin.ModelAdmin):

    list_display = ('sök_term',
                    'ip_adress',
                    'sök_timestamp')

class SökDataAdmin(admin.ModelAdmin):

    list_display = ('sök_term',
                    'ip_adress',
                    'sök_timestamp',
                    'records_returned')



admin.site.register(Begrepp, BegreppAdmin)
admin.site.register(Bestallare, BestallareAdmin)
admin.site.register(Doman, DomanAdmin)
admin.site.register(Synonym, SynonymAdmin)
admin.site.register(OpponeraBegreppDefinition, OpponeraBegreppDefinitionAdmin)
admin.site.register(SökFörklaring, SökFörklaringAdmin)
admin.site.register(SökData, SökDataAdmin)



