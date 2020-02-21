import json
from pdb import set_trace

from django.forms.models import model_to_dict
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from datetime import datetime
from django.db import connection, transaction
from django.core.mail import EmailMessage
from ordbok.models import Begrepp, Bestallare, Doman, Synonym, OpponeraBegreppDefinition
from ordbok import models
from .forms import TermRequestForm, OpponeraTermForm, BekräftaTermForm, OpponeraTermForm
import re
import logging
from bs4 import BeautifulSoup


logger = logging.getLogger(__name__)


re_pattern = re.compile(r'\s+')

def retur_komplett_förklaring_custom_sql(url_parameter):
    
    cursor = connection.cursor()
    sql_statement = f'''SELECT\
                            begrepp_kontext,\
                            begrepp_version_nummer,\
                            definition,\
                            externt_id,\
                            externt_register,\
                            status,\
                            term,\
                            utländsk_definition,\
                            utländsk_term,\
                            vgr_id,\
                            synonym,\
                            domän_namn\
                            FROM\
                                ordbok_begrepp\
                            LEFT JOIN\
                                ordbok_synonym\
                                ON ordbok_begrepp.id = ordbok_synonym.begrepp_id\
                            LEFT JOIN\
                                ordbok_doman\
                                ON ordbok_begrepp.id = ordbok_doman.begrepp_id\
                            WHERE\
                                ordbok_begrepp.id = {url_parameter};'''
    
    column_names = ['begrepp_kontext',
                   'begrepp_version_nummer',
                   'definition',
                   'externt_id',
                   'externt_register',
                   'status',
                   'term',
                   'utländsk_definition',
                   'utländsk_term',
                   'vgr_id',
                   'synonym',
                   'domän_namn']

    clean_statement = re.sub(re_pattern, ' ', sql_statement)
    cursor.execute(clean_statement)
    result = cursor.fetchall()
    
    #column_names = [i[0] for i in result.description]
    #retur_records = result.fetchall()
    
    return dict(zip(column_names, result[0]))

def begrepp_view(request):
    ctx = {}
    url_parameter = request.GET.get("q")
    logger.error('Test')
    if url_parameter:
        begrepp = Begrepp.objects.filter(term__icontains=url_parameter)
    else:
        begrepp = Begrepp.objects.all()

    ctx["begrepp"] = begrepp
    if request.is_ajax():

        html = render_to_string(
            template_name="term-results-partial.html", context={"begrepp": begrepp}
        )
        data_dict = {"html_from_view": html}
        return JsonResponse(data=data_dict, safe=False)

    return render(request, "term.html", context=ctx)

def begrepp_förklaring_view(request):
    ctx = {}
    url_parameter = request.GET.get("q")
    
    if url_parameter:
        exact_term = retur_komplett_förklaring_custom_sql(url_parameter)
    else:
        term_json = 'Error - Record not found'
    
    if request.is_ajax():
        html = render_to_string(template_name="term_forklaring.html", context={"begrepp": exact_term})
        data_dict = {"html_from_view": html}
        
        return HttpResponse(json.dumps(data_dict), content_type="application/json")

    return render(request, "base.html", context=ctx)

def hantera_request_term(request):
    
    if request.method == 'POST':
        form = TermRequestForm(request.POST)
        if form.is_valid():

            ny_beställare = Bestallare()
            ny_beställare.beställare_datum = datetime.now().strftime("%Y-%m-%d %H:%M")
            ny_beställare.beställare_namn = form.clean_name()
            ny_beställare.beställare_email = form.clean_epost()
            ny_beställare.beställare_telefon = form.clean_telefon()
            ny_beställare.save()

            ny_term = Begrepp()
            ny_term.term = form.cleaned_data.get('begrepp')
            ny_term.begrepp_kontext = request.POST.get('kontext')
            ny_term.begrepp_version_nummer = datetime.now().strftime("%Y-%m-%d %H:%M")
            ny_term.beställare = ny_beställare
            ny_term.save()

            inkommande_domän = Doman()
            
            inkommande_domän.domän_namn = form.cleaned_data.get('workstream')
            inkommande_domän.domän_kontext = form.cleaned_data.get('workflow_namn')
            inkommande_domän.begrepp = ny_term
            inkommande_domän.save()

            return HttpResponse('Tack! Begrepp skickades in för granskning')

    else:
        form = TermRequestForm()
    
    return render(request, 'requestTerm.html', {'form': form})

def opponera_term(request):

    url_parameter = request.GET.get("q")

    if request.method == 'GET':
        inkommande_term = Begrepp(term=url_parameter)
        form = OpponeraTermForm(initial={'term' : inkommande_term})

    if request.method == 'POST':
        form = OpponeraTermForm(request.POST)
        if form.is_valid():
            
            opponera_term = OpponeraBegreppDefinition()
            opponera_term.begrepp_kontext = form.cleaned_data.get('resonemang')
            opponera_term.datum = datetime.now().strftime("%Y-%m-%d %H:%M")
            opponera_term.epost = form.cleaned_data.get('epost')
            opponera_term.namn = form.cleaned_data.get('namn')
            opponera_term.status = models.DEFAULT_STATUS
            opponera_term.telefon = form.cleaned_data.get('telefon')
            # entries with doublets cause a problem, so we take the first one
            opponera_term.begrepp = Begrepp.objects.filter(term=form.cleaned_data.get('term')).first()
            opponera_term.save()

            return HttpResponse('Tack! Dina synpunkter har skickats in')
    
    return render(request, 'opponera_term.html', {'opponera': form})

def bekräfta_term(request):

    url_parameter = request.GET.get("q")

    if request.method == 'GET':
        inkommande_term = Begrepp(term=url_parameter)
        form = BekräftaTermForm(initial={'term' : inkommande_term})

    if request.method == 'POST':
        form = BekräftaTermForm(request.POST)
        if form.is_valid():
            kopplad_domän = Doman()
            kopplad_domän.begrepp = Begrepp.objects.filter(term=form.cleaned_data.get('term')).first()
            kopplad_domän.domän_namn = form.cleaned_data.get('workstream')
            kopplad_domän.domän_kontext = form.cleaned_data.get('kontext')

            # We need to clean out the "Inte definierad" once the domän has been given a real one
            #SomeModel.objects.filter(id=id).delete()
 
            kopplad_domän.save()
            return HttpResponse('Tack! Användingen av begreppet i arbetsströmen bekräftades')
    else:
        return render(request, 'bekrafta_term.html', {'bekräfta': form})