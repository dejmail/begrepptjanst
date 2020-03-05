from pdb import set_trace
from .models import SökData, SökFörklaring

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