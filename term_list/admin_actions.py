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

import logging
from pdb import set_trace

from term_list.models import Dictionary, Concept, Synonym
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
                               'utländsk_term',
                               'annan_ordlista',
                               'externt_id',
                               'senaste_ändring',
                               'begrepp_version_nummer',
                               'datum_skapat',
                               'term_i_system',
                               'tidigare_definition_och_källa',
                               'id']

def get_synonym_set(obj):
    
    query = getattr(obj, 'synonym_set')
    return_list = []
    for synonym in query.values_list('synonym','synonym_status'):
        return_list.append(f'{synonym[0]} - {synonym[1]}')
    if len(return_list) > 0:
        return ', '.join(return_list)
    else:
        return ''

def export_chosen_begrepp_as_csv(request, queryset, field_names='all'):

    
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output)
    worksheet = workbook.add_worksheet()
    bold = workbook.add_format({'bold': True})
    date_format = workbook.add_format({'num_format': 'YYYY-MM-DD H:M:S'})

    chosen_columns = [i for i in predetermined_column_order if i in field_names]
    zipped_list = zip(chosen_columns, field_names)
    field_names = [x[0] for x in zipped_list]
    logger.debug(f"column order of export file --> {field_names}")
    row_index=0
    col_index=0
    worksheet.write_row(row_index,col_index,field_names, bold)
    length=40

    for obj in queryset:
        row_index += 1
        worksheet.set_row(row_index, 15)
        for col_index, field in enumerate(field_names):
            worksheet.set_column(row_index, col_index, length)
            if field == 'synonym':
                field_value = get_synonym_set(obj)
                worksheet.write(row_index, col_index, field_value)
                logger.debug(f'writing {field} - {field_value}')
            elif field == 'term':
                field_value = getattr(obj, field)
                link = request.build_absolute_uri(reverse('term_metadata'))  + f'?q={obj.pk}'
                worksheet.write_url(row=row_index, col=col_index, url=link, string=field_value)
                logger.debug(f'writing {field} - {field_value}')
            elif field == 'beställare':
                field_value = getattr(obj, field).beställare_namn
                worksheet.write(row_index, col_index, field_value)
                logger.debug(f'writing {field} - {field_value}')
            elif field in ['datum_skapat', 'begrepp_version_nummer']:
                field_value = getattr(obj, field)
                worksheet.write(row_index, col_index, field_value, date_format)
            else:
                field_value = getattr(obj, field)
                if (type(field_value) == str) and (len(field_value) > 80):
                    worksheet.set_column(col_index, col_index, length)
                    worksheet.write(row_index, col_index, field_value)
                else:
                    worksheet.write(row_index, col_index, field_value)
                logger.debug(f'writing {field} - {field_value}')
    workbook.close()
    output.seek(0)

    filename = f"{queryset.first()._meta.object_name.lower()}_export_{datetime.datetime.now().strftime('%Y_%m_%d-%H:%M:%S')}.xlsx"
    logger.debug(f"field_names for ACTION begrepp_export - {field_names}")
    response = HttpResponse(
        output, 
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

    response['Content-Disposition'] = f'attachment; filename={filename}'

    return response

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
