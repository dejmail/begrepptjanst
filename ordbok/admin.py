from django.contrib import admin
from ordbok.models import Begrepp, Bestallare, Doman, OpponeraBegreppDefinition, Synonym

admin.site.site_header = "BegreppTjänst Admin"
admin.site.site_title = "BegpreppTjänst Admin Portal"
admin.site.index_title = "Välkommen till BegreppTjänst Portalen"

class BegreppAdmin(admin.ModelAdmin):
    list_display = ('term',
                    'definition',
                    'begrepp_kontext',    
                    'externt_register',
                    'term',
                    'utländsk_definition',
                    'utländsk_term',
                    'begrepp_version_nummer',
                    'status',)

    list_filter = ("begrepp_version_nummer", "status",)

    search_fields = ('term',
                    'definition',
                    'begrepp_kontext',    
                    'externt_register',
                    'term',
                    'utländsk_definition',
                    'utländsk_term',
                    'begrepp_version_nummer',
                    'status',)

    date_hierarchy = 'begrepp_version_nummer'


class BestallareAdmin(admin.ModelAdmin):

    list_display = ('beställare_namn',
                    'beställare_email',
                    'beställare_telefon',
                    'beställare_datum',)

class DomanAdmin(admin.ModelAdmin):

    list_display = ('domän_namn',
                    'domän_id',
                    'domän_kontext',
                    'begrepp',)

    list_filter = ("domän_namn",)
    search_fields = ('begrepp__term',)

class SynonymAdmin(admin.ModelAdmin):

    list_display = ('begrepp',
                    'synonym',
                    'synonym_status')

    list_filter = ("synonym_status",)
    search_fields = ("begrepp__term",)

class OpponeraBegreppDefinitionAdmin(admin.ModelAdmin):

    list_display = ('begrepp',
                    'begrepp_kontext',
                    'datum',
                    'epost',
                    'namn',
                    'status',
                    'telefon')

admin.site.register(Begrepp, BegreppAdmin)
admin.site.register(Bestallare, BestallareAdmin)
admin.site.register(Doman, DomanAdmin)
admin.site.register(Synonym, SynonymAdmin)
admin.site.register(OpponeraBegreppDefinition, OpponeraBegreppDefinitionAdmin)
