from pdb import set_trace
from .models import SökData, SökFörklaring

from .models import SökData, SökFörklaring, Bestallare

from django.core import mail
from django.core.mail import EmailMultiAlternatives, get_connection, send_mail


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

def skicka_epost_till_beställaren(queryset):

    email_list = []

    for enskilda_term in queryset.select_related():
        beställare = Bestallare.objects.get(id=enskilda_term.beställare_id)
        subject, from_email, to = 'Uppdatering av term status', 'info@vgrinformatik.se', beställare.beställare_email
        text_content = f'''Begreppet <strong>{enskilda_term.term}</strong> du skickade in har ändrats sin status. Det står nu som <strong>{enskilda_term.status}</strong>.<br>
        <p>Om du vill läsa mer detaljer, vänligen navigera till OLLI och söka på termen.</p>

        <p><a href="http://vgrinformatik.se/begreppstjanst">OLLI Begreppstjanst</a></p>

        '''
        html_content = f'<p>{text_content}</p>'
        msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
        msg.attach_alternative(html_content, "text/html")
        email_list.append(msg)

    with mail.get_connection() as connection:
        connection.send_messages(email_list)
        connection.close()