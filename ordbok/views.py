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
from .functions import mäta_sök_träff, mäta_förklaring_träff
import re
import logging


logger = logging.getLogger(__name__)


re_pattern = re.compile(r'\s+')

def extract_columns_from_query_and_return_set(search_result, start, stop):

    reduced_list = []
    for record in search_result:
        if start==0:
            reduced_list.append(record[:stop])
        elif stop==0:
            reduced_list.append(record[start:])
        else:
            reduced_list.append(record[start:stop])
    
    reduced_set = set([tuple(i) for i in reduced_list])
    return  reduced_set


def retur_general_sök(url_parameter):
    cursor = connection.cursor()
    ''' need to reduce the number of fields being returned, we are not using all of them,
    but this also affects the parsing as it is position based, so need to be careful'''
    sql_statement = f'''SELECT ordbok_begrepp.id,\
                              definition,\
                              term,\
                              ordbok_begrepp.status,\
                              ordbok_synonym.begrepp_id AS synonym_begrepp_id,\
                              synonym,\
                              synonym_status\
                        FROM ordbok_begrepp\
                            LEFT JOIN ordbok_synonym\
                                ON ordbok_begrepp.id = ordbok_synonym.begrepp_id\
                            LEFT JOIN ordbok_doman\
                                ON ordbok_begrepp.id = ordbok_doman.begrepp_id\
                        WHERE ordbok_begrepp.term LIKE "%{url_parameter}%"\
                        OR ordbok_begrepp.utländsk_term LIKE "%{url_parameter}%"\
                        OR ordbok_synonym.synonym LIKE "%{url_parameter}%";'''

    column_names = ['begrepp_id',
                    'definition',
                    'term',
                    'begrepp_id',                    
                    'synonym',
                    'synonym_status']

    clean_statement = re.sub(re_pattern, ' ', sql_statement)
    
    cursor.execute(clean_statement)
    result = cursor.fetchall()
    
    return result
    

def retur_komplett_förklaring_custom_sql(url_parameter):
    
    cursor = connection.cursor()
    sql_statement = f'''SELECT\
                            ordbok_begrepp.id AS begrepp_id,\
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
                            anmärkningar,\
                            ordbok_synonym.begrepp_id AS synonym_begrepp_id,\
                            synonym,
                            synonym_status,\
                            ordbok_doman.begrepp_id AS domän_begrepp_id,\
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

    clean_statement = re.sub(re_pattern, ' ', sql_statement)
    cursor.execute(clean_statement)
    result = cursor.fetchall()
    
    return result

def run_sql_statement(sql_statement):

        cursor = connection.cursor()
        clean_statement = re.sub(re_pattern, ' ', sql_statement)
        cursor.execute(clean_statement)
        result = cursor.fetchall()

        return result

def begrepp_view(request):
    ctx = {}
    url_parameter = request.GET.get("q")

    if request.is_ajax():
        search_request = retur_general_sök(url_parameter)

        begrepp = extract_columns_from_query_and_return_set(search_result=search_request, start=0, stop=3)
        synonym = extract_columns_from_query_and_return_set(search_result=search_request, start=4, stop=7)

        begrepp_column_names = ['begrepp_id', 'definition', 'term']
    
        return_list_dict = []
        for return_result in begrepp:
            return_list_dict.append(dict(zip(begrepp_column_names, return_result)))

        synonym_column_names = ['begrepp_id', 'synonym', 'synonym_status']

        return_synonym_list_dict = []
        for return_result in synonym:
            return_synonym_list_dict.append(dict(zip(synonym_column_names, return_result)))
    

        html = render_to_string(
            template_name="term-results-partial.html", context={'begrepp': return_list_dict,
                                                                'synonym' : return_synonym_list_dict}
        )
        data_dict = {"html_from_view": html}
        
        mäta_sök_träff(sök_term=url_parameter,sök_data=return_list_dict, request=request)

        return JsonResponse(data=data_dict, safe=False)
    
    else:
        begrepp = Begrepp.objects.none()

    return render(request, "term.html", context={'begrepp': begrepp})

def begrepp_förklaring_view(request):
    ctx = {}
    url_parameter = request.GET.get("q")
    
    if url_parameter:
        exact_term_request = retur_komplett_förklaring_custom_sql(url_parameter)
        begrepp_full = extract_columns_from_query_and_return_set(exact_term_request, 0, -5)
        synonym_full = extract_columns_from_query_and_return_set(exact_term_request, -5, -2)
        domän_full = extract_columns_from_query_and_return_set(exact_term_request, -2, 0)

        result_column_names = ['begrepp_id',
                               'begrepp_kontext',
                               'begrepp_version_nummer',
                               'definition',
                               'externt_id',
                               'externt_register',
                               'status',
                               'term',
                               'utländsk_definition',
                               'utländsk_term',
                               'vgr_id',
                               'anmärkningar',
                               'synonym_begrepp_id',
                               'synonym',
                               'synonym_status',
                               'domän_begrepp_id',
                               'domän_namn']

        begrepp_column_names = result_column_names[:-5]
        return_list_dict = []
        for return_result in begrepp_full:
            return_list_dict.append(dict(zip(begrepp_column_names, return_result)))

        synonym_column_names = result_column_names[-5:-2]
        return_synonym_list_dict = []
        for return_result in synonym_full:
            return_synonym_list_dict.append(dict(zip(synonym_column_names, return_result)))
        

        domän_column_names = result_column_names[-2:]
        return_domän_list_dict = []
        for return_result in domän_full:
            return_domän_list_dict.append(dict(zip(domän_column_names, return_result)))

        mäta_förklaring_träff(sök_term=url_parameter, request=request)
        
    else:
        term_json = Begrepp.objects.none()
    
    if request.is_ajax():
        #set_trace()
        html = render_to_string(template_name="term_forklaring.html", context={'begrepp_full': return_list_dict[0],
                                                                               'synonym_full' : return_synonym_list_dict,
                                                                               'domän_full' : return_domän_list_dict})
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

            return HttpResponse('''<div class="alert alert-success">
                                   Tack! Begrepp skickades in för granskning.
                                   </div>''')

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

            return HttpResponse('''<div class="alert alert-success">
                                   Tack för dina synpunkter.
                                   </div>''')
    
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
            if kopplad_domän.domän_namn == 'Inte relevant':
                kopplad_domän.domän_namn = form.cleaned_data.get('kontext')
                kopplad_domän.domän_kontext = '-'
            else:
                kopplad_domän.domän_namn = form.cleaned_data.get('kontext')

            # We need to clean out the "Inte definierad" once the domän has been given a real one
            #SomeModel.objects.filter(id=id).delete()
 
            kopplad_domän.save()
            return HttpResponse('''<div class="alert alert-success">
                                   Tack för verifiering av domänen.
                                   </div>''')
    else:
        return render(request, 'bekrafta_term.html', {'bekräfta': form})