from pdb import set_trace
from .models import SökData, SökFörklaring, Bestallare

from django.core import mail
from django.core.mail import EmailMultiAlternatives, get_connection, send_mail
import re
import datetime

def besökare_ip_adress(request):

    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')

    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def mäta_sök_träff(sök_term, sök_data, request):

    ny_sök = SökData()
    ny_sök.sök_term = sök_term
    ny_sök.records_returned = str([i.get('begrepp_id') for i in sök_data])[1:-1]
    ny_sök.ip_adress = besökare_ip_adress(request)
    ny_sök.save()
    return None

def mäta_förklaring_träff(sök_term, request):

    ny_sök = SökFörklaring()
    ny_sök.sök_term = sök_term
    ny_sök.ip_adress = besökare_ip_adress(request)
    ny_sök.save()

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

<br><br>Kommentar från informatik:<br> {enskilda_term.email_extra}<br><br>

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

def nbsp2space(string_with_bad_values):
    
    return re.sub('\\xa0', ' ', string_with_bad_values, flags=re.IGNORECASE|re.UNICODE)

class Xlator(dict):
    """ All-in-one multiple-string-substitution class
        a version to substitute only entire words """

    def escape_keys(self):
        
        return [re.escape(i) for i in self.keys()]

    def _make_regex(self):
        
        escaped_keys = self.escape_keys()
        joined_keys = r'\b'+r'\b|\b'.join(escaped_keys)
        compiled_re = re.compile(joined_keys+r'\b')
        
        return compiled_re

    def __call__(self, match):
        """ Handler invoked for each regex match """
        return self[match.group(0)]

    def xlat(self, text):
        """ Translate text, returns the modified text. """
        return self._make_regex().sub(self, text)
