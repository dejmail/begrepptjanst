from django.http import HttpResponse
from django.urls import reverse
from django.shortcuts import render, redirect

from .models import TaskOrderer

from django.core import mail
from django.core.mail import EmailMultiAlternatives, get_connection, message, send_mail
from django.contrib import messages


import io
import xlsxwriter
import datetime
import pandas as pd
from django.db import transaction


import logging
from pdb import set_trace
from typing import List
from django.db.models import QuerySet
from django.http import HttpRequest
import traceback

from django.contrib.admin.utils import get_deleted_objects
from django.contrib.admin import helpers
from django.template.response import TemplateResponse
from django.core.exceptions import PermissionDenied
from django.db import router, transaction
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html


from term_list.models import Dictionary, Attribute
from term_list.forms import ColumnMappingForm, ExcelImportForm

logger = logging.getLogger(__name__)

predetermined_column_order =  ['id_vgr',
                               'term',
                               'synonym',
                               'definition',
                               'källa',
                               'anmärkningar',
                               'status',
                               'beställare',
                               'begrepp_kontext',
                               'kommentar_handläggning',
                               'non_swedish_terrm',
                               'annan_ordlista',
                               'externt_id',
                               'senaste_ändring',
                               'begrepp_version_nummer',
                               'datum_skapat',
                               'term_i_system',
                               'tidigare_definition_och_källa',
                               'id']

def get_synonym_set(obj):
    
    query = getattr(obj, 'synonyms')
    return_list = []
    for synonym in query.values_list('synonym','synonym_status'):
        return_list.append(f'{synonym[0]} - {synonym[1]}')
    if len(return_list) > 0:
        return ', '.join(return_list)
    else:
        return ''

def export_chosen_concept_as_csv(request: HttpRequest, 
                                 queryset : QuerySet,
                                 selected_fields : List[str],
                                 field_mapping: Dictionary):

    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output)
    worksheet = workbook.add_worksheet()
    date_format = workbook.add_format({'num_format': 'YYYY-MM-DD HH:MM:SS'})

    # Formatting
    bold = workbook.add_format({'bold': True})

    # Write Header Row
    worksheet.write_row(0, 0, selected_fields, bold)

    # Write Data Rows
    for row_idx, obj in enumerate(queryset, start=1):
        for col_index, field in enumerate(selected_fields):
            if field.lower() == 'synonyms':
                row_data = get_synonym_set(obj)
                worksheet.write(row_idx, col_index, row_data)
            elif field.lower() == 'term':
                row_data = getattr(obj, field.lower(), "")
                link = request.build_absolute_uri(reverse('term_metadata'))  + f'?q={obj.pk}'
                worksheet.write_url(row=row_idx, col=col_index, url=link, string=row_data)
            elif (field in field_mapping.keys()) and (field in ['Senaste ändring', 'Datum skapat']):
                logger.debug('Found date, fixing format')
                row_data = getattr(obj, field_mapping.get(field))
                worksheet.write(row_idx, col_index, row_data, date_format)
            elif field.lower() == 'dictionaries':
                row_data = ', '.join([dictionary.dictionary_name for dictionary in obj.dictionaries.all()])
                worksheet.write(row_idx, col_index, row_data)
            else:
                if hasattr(obj, field.lower()):
                    row_data = getattr(obj, field.lower(), "")                
                else:
                    matching_attr = next((attr for attr in obj.attributes.all() if attr.attribute.display_name == field), None)
                    row_data = matching_attr.get_value() if matching_attr else ""

                worksheet.write(row_idx, col_index, row_data)

    workbook.close()
    output.seek(0)

    # Prepare Response
    response = HttpResponse(output, content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response["Content-Disposition"] = f'attachment; filename="exporterad_begrepp_{datetime.datetime.now().strftime("%Y_%m_%d-%H:%M:%S")}.xlsx"'
    
    return response

def delete_allowed_concepts(modeladmin, request, queryset):

    opts = modeladmin.model._meta
    app_label = opts.app_label

    accessible_dictionaries = modeladmin.get_accessible_dictionaries(request)
    deletable = [obj for obj in queryset if modeladmin._user_has_dictionary_access(request, obj)]

    if not deletable:
        modeladmin.message_user(
            request,
                "Inga av de valda begreppen kan raderas baserat på dina gruppbehörigheter.",
            level=messages.WARNING
        )
        return

    if request.POST.get("post"):
        try:
            with transaction.atomic():
                count = len(deletable)
                for obj in deletable:
                    obj.delete()
                modeladmin.message_user(
                    request,
                    f"Raderade {count} begrepp/term.",
                    level=messages.SUCCESS
                )
        except Exception as e:
            modeladmin.message_user(
                request,
                f"Ett fel uppstod under radering: {str(e)}",
                level=messages.ERROR
            )
        return None
    
    using = router.db_for_write(modeladmin.model)
    try:
        deletable_objects, model_count, perms_needed, protected = get_deleted_objects(
            objs=deletable,
            request=request,
            admin_site=modeladmin.admin_site
        )
        logger.debug(f'{perms_needed=}')
    except Exception as e:
        traceback.print_exc()
        raise
    
    if perms_needed:
        raise PermissionDenied(
            "Du har inte tillräckliga rättigheter för att radera dessa objekt."
        )
    
    context = {
        **modeladmin.admin_site.each_context(request),
        "title": _("Är du säker?"),
        "objects_name": str(opts.verbose_name_plural),
        "deletable_objects": deletable_objects,
        "queryset": deletable,
        "opts": opts,
        "app_label": app_label,
        "action_checkbox_name": helpers.ACTION_CHECKBOX_NAME,
    }

    return TemplateResponse(
        request,
        "admin/delete_selected_intermediate.html",
        context
    )


delete_allowed_concepts.short_description = "Radera valda begrepp (om tillåtet)"



def change_dictionaries(modeladmin, request, queryset):
    logger = logging.getLogger(__name__)

    logger.info("change_dictionaries action called.")

    if 'apply' in request.POST:
        selected_dictionaries = request.POST.getlist('dictionaries')
        if selected_dictionaries:
            dictionaries = Dictionary.objects.filter(pk__in=selected_dictionaries)
            for begrepp in queryset:
                begrepp.dictionaries.set(dictionaries)
            modeladmin.message_user(request, f"{queryset.count()} Begrepp updated with the selected Dictionaries.")
        return redirect(request.get_full_path())

    # Prepare context including _selected_action and select_across
    context = {
        'queryset': queryset,
        'dictionaries': Dictionary.objects.all(),
        'action_name': 'change_dictionaries',
        'selected_action': request.POST.getlist('_selected_action'),
        'select_across': request.POST.get('select_across'),
    }
    return render(request, 'admin/change_dictionary_action.html', context)

change_dictionaries.short_description = "Change Dictionaries of selected Begrepp"


def export_chosen_concepts_action(modeladmin, request, queryset):

    db_table_attrs = [
    field.verbose_name.capitalize() if hasattr(field, "verbose_name") and field.verbose_name else field.name.capitalize()
    for field in queryset.first()._meta.get_fields()
    if field.name not in ['concept_fk', 'conceptcomment', 'conceptexternalfiles', 'attributes']
    ]
    
    attribute_names = Attribute.objects.filter(
        attributevalue__term__in=queryset
    ).values_list('display_name', flat=True).distinct()

    db_table_attrs.extend(attribute_names)
    chosen_concepts = [{'pk': i[0], 'term': i[1]} for i in queryset.values_list('pk', 'term')]
    
    return render(request, "choose_export_attrs_intermediate.html", context={"db_table_attrs" : db_table_attrs,
                                                                            "chosen_concepts" : chosen_concepts})

export_chosen_concepts_action.short_description = "Exportera valde begrepp"

def ändra_status_till_översättning(queryset):
    
    queryset.update(status='Översättning')
    

def skicka_epost_till_beställaren_status(queryset):

    email_list = []

    for enskilda_term in queryset.select_related():
        beställare = TaskOrderer.objects.get(id=enskilda_term.beställare_id)
        subject, from_email, to = 'Uppdatering av term status i Olli', 'info@vgrinformatik.se', beställare.beställare_email
        text_content = f'''Hej!<br>Begreppet <strong>{enskilda_term.term}</strong> du skickade in har ändrats sin status. Det står nu som <strong>{enskilda_term.status}</strong>.<br>
        <br>Kommentar från informatik:<br> {enskilda_term.email_extra}<br><br>

        

        <p><a href="https://vgrinformatik.se/begreppstjanst/begrepp_forklaring/?q={enskilda_term.id}">Klicka här för att komma direkt till ditt efterfrågade begrepp</a></p>
        
        
<br>Med vänlig hälsning <br>

Projekt för informatik inom vård och omsorg i Västra Götaland

        '''
        html_content = f'<p>{text_content}</p>'
        msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
        msg.attach_alternative(html_content, "text/html")
        email_list.append(msg)

    with mail.get_connection() as connection:
        connection.send_messages(email_list)
        connection.close()

def skicka_epost_till_beställaren_validate(queryset):

    email_list = []

    for enskilda_term in queryset.select_related():
        beställare = TaskOrderer.objects.get(id=enskilda_term.beställare_id)
        subject, from_email, to = 'Begrepp för validering i OLLI', 'info@vgrinformatik.se', beställare.beställare_email
        text_content = f'''Hej! <br>

Begreppet <strong>{enskilda_term.term}</strong> har nu hanterats av informatikprojektet och vi önskar validering från verksamheten innan det beslutas. Du som framfört önskemål om begreppet ansvarar för förankring i verksamheten och vi ber dig därför gå igenom begreppet i OLLI och kontrollera om du tycker att det stämmer överens med hur verksamheten vill använda begreppet. 

<br><br>Kommentar från informatik:<br> {enskilda_term.email_extra}<br><br>  

Eventuella synpunkter lämnas som svar på detta mejl. 


<p><a href="https://vgrinformatik.se/begreppstjanst/begrepp_forklaring/?q={enskilda_term.id}">Länk till begreppet</a></p>

Tack för din hjälp! <br>

 

Med vänlig hälsning <br>

Projekt för informatik inom vård och omsorg i Västra Götaland
        '''
        html_content = f'<p>{text_content}</p>'
        msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
        msg.attach_alternative(html_content, "text/html")
        email_list.append(msg)
    with mail.get_connection() as connection:
        connection.send_messages(email_list)
        connection.close()

def skicka_epost_till_beställaren_beslutad(queryset):

    email_list = []

    for enskilda_term in queryset.select_related():
        beställare = TaskOrderer.objects.get(id=enskilda_term.beställare_id)
        subject, from_email, to = 'Beslutat begrepp i OLLI', 'info@vgrinformatik.se', beställare.beställare_email
        text_content = f'''  

Hej! <br>

Begreppet {enskilda_term.term} har definierats och beslutats i OLLI. 

<br><br>Kommentar från informatik:<br> {enskilda_term.email_extra}<br><br><br>
Om ni har synpunkter på definitionen vänligen återkoppla till informatik genom att svara på detta mail.<br>

<p><a href="https://vgrinformatik.se/begreppstjanst/begrepp_forklaring/?q={enskilda_term.id}">Länk till begreppet</a></p> 
 <br>
Med vänlig hälsning <br>

Projekt för informatik inom vård och omsorg i Västra Götaland 
        '''
        html_content = f'<p>{text_content}</p>'
        msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
        msg.attach_alternative(html_content, "text/html")
        email_list.append(msg)

    with mail.get_connection() as connection:
        connection.send_messages(email_list)
        connection.close()
