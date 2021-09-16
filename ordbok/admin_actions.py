from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext, loader
from django.urls import reverse
from django.shortcuts import render
from django.contrib.contenttypes.models import ContentType
from .models import Bestallare

from django.core import mail
from django.core.mail import EmailMultiAlternatives, get_connection, message, send_mail

import codecs
import csv
import datetime

from .forms import ChooseExportAttributes

import logging
from pdb import set_trace

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
                               'begrepp_version_nummer',
                               'datum_skapat',
                               'term_i_system',
                               'utländsk_definition',
                               'alternativ_definition',
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

    filename = f"{queryset.first()._meta.object_name.lower()}_export_{datetime.datetime.now().strftime('%Y_%m_%d-%H:%M:%S')}.csv"
    logger.debug(f"field_names for ACTION begrepp_export - {field_names}")

    response = HttpResponse(content_type='text/txt')
    response['Content-Disposition'] = f'attachment; filename={filename}'
    response.write(codecs.BOM_UTF8)
    writer = csv.writer(response, dialect="excel", quotechar='"')
    
    chosen_columns = [i for i in predetermined_column_order if i in field_names]
    zipped_list = zip(chosen_columns, field_names)
    field_names = [x[0] for x in zipped_list]
    logger.debug(f"column order of export file --> {field_names}")

    writer.writerow(field_names)
    for obj in queryset:
        row = []
        
        for field in field_names:
            if field == 'synonym':
                field_value = get_synonym_set(obj)
                row.append(field_value)
                logger.debug(f'writing {field} - {field_value}')
            elif field == 'term':
                field_value = getattr(obj, field)
                row.append(field_value)
                logger.debug(f'writing {field} - {field_value}')
            else:
                field_value = getattr(obj, field)
                row.append(field_value)
                logger.debug(f'writing {field} - {field_value}')

        writer.writerow(row)

    return response

def ändra_status_till_översättning(queryset):
    
    queryset.update(status='Översättning')
    


def skicka_epost_till_beställaren_status(queryset):

    email_list = []

    for enskilda_term in queryset.select_related():
        beställare = Bestallare.objects.get(id=enskilda_term.beställare_id)
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
        beställare = Bestallare.objects.get(id=enskilda_term.beställare_id)
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
        beställare = Bestallare.objects.get(id=enskilda_term.beställare_id)
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
