import json
from pdb import set_trace


from django.forms.models import model_to_dict
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from datetime import datetime
from django.db import connection, transaction
from django.db.models import Q
from django.core.mail import EmailMessage

from django.core.files.storage import FileSystemStorage
from django.conf import settings

from ordbok.models import *
from ordbok import models
from .forms import TermRequestForm, TermRequestTranslateForm, BekräftaTermForm, OpponeraTermForm
from .functions import mäta_sök_träff, mäta_förklaring_träff, Xlator, nbsp2space

import re
import logging
from begrepptjanst.logs import setup_logging
from django.utils.html import format_html

logger = logging.getLogger(__name__)


re_pattern = re.compile(r'\s+')

färg_status_dict = {'Avråds' : 'table-danger',
                    'Beslutad': 'table-success',
                    'Pågår': 'table-warning',
                    'Preliminär': 'table-warning',
                    'Ej Påbörjad': 'table-warning',
                    'Definieras ej': 'table-warning-light',
                    'Publiceras ej' : 'table-light-blue'}

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
    return reduced_set


def retur_general_sök(url_parameter):
    cursor = connection.cursor()
    ''' need to reduce the number of fields being returned, we are not using all of them,
    but this also affects the parsing as it is position based, so need to be careful'''
    sql_statement = f'''SELECT ordbok_begrepp.id,\
                              definition,\
                              term,\
                              utländsk_term,\
                              ordbok_begrepp.status AS begrepp_status,\
                              ordbok_synonym.begrepp_id AS synonym_begrepp_id,\
                              synonym,\
                              synonym_status\
                        FROM ordbok_begrepp\
                            LEFT JOIN ordbok_synonym\
                                ON ordbok_begrepp.id = ordbok_synonym.begrepp_id\
                            LEFT JOIN ordbok_doman\
                                ON ordbok_begrepp.id = ordbok_doman.begrepp_id\
                        WHERE (ordbok_begrepp.term LIKE "%{url_parameter}%" AND NOT ordbok_begrepp.status = 'Publicera ej')\
                        OR (ordbok_begrepp.definition LIKE "%{url_parameter}%" AND NOT ordbok_begrepp.status = 'Publicera ej')\
                        OR ordbok_begrepp.utländsk_term LIKE "%{url_parameter}%"\
                        OR ordbok_synonym.synonym LIKE "%{url_parameter}%";'''
    
    column_names = ['begrepp_id',
                    'definition',
                    'term',
                    'utländsk_term',
                    'begrepp_status', 
                    'synonym_begrepp_id',
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
                            källa,\
                            validated_by,\
                            term_i_system,\
                            externt_id,\
                            annan_ordlista,\
                            status,\
                            term,\
                            utländsk_definition,\
                            utländsk_term,\
                            id_vgr,\
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


def sort_returned_sql_search_according_to_search_term_position(lines, delim, position=1):
    
    '''
    Returns a sorted list based on "column" from list-of-dictionaries data.
    '''

    return sorted(lines, key=lambda x: x.get('term').split(delim))


def highlight_search_term_i_definition(search_term, begrepp_dict_list):

    for idx, begrepp in enumerate(begrepp_dict_list):
        begrepp_dict_list[idx]['definition'] = format_html(begrepp.get('definition').replace(search_term, f'<mark>{search_term}</mark>'))
        
    return begrepp_dict_list


def return_list_of_term_and_definition():
    
    cursor = connection.cursor()
    sql_statement = f"SELECT term, definition FROM ordbok_begrepp;"
    clean_statement = re.sub(re_pattern, ' ', sql_statement)
    cursor.execute(clean_statement)
    result = cursor.fetchall()

    return result

def clean_dict_of_extra_characters(incoming_dict):

    clean_dict = {}
    for keys,values in incoming_dict.items():
        clean_dict[keys.strip()] = re.sub('\xa0', ' ', values)
    return clean_dict

def creating_tooltip_hover_with_definition_of_all_terms_present_in_search_result(begrepp_dict_list, term_def_dict):

    #create a set as there are duplicates in the database
    term_def_set = set([(concepts,definition) for concepts,definition in term_def_dict])
    # create a dictionary with the term as key and definition containing the HTML needed to show the hover definition
    term_def_dict_uncleaned = {concept:f'''<div class="definitiontooltip">{concept.strip()}<div class="definitiontooltiptext">{definition}</div></div>''' for concept, definition in term_def_set}
    
    term_def_dict = clean_dict_of_extra_characters(term_def_dict_uncleaned)

    # Would be good to be able to send a list of plurals that we could 
    # group togther in the pattern creation, but as Xlator is a dict
    # class, I'm not sure how to do that-

    #plurals = {'hälso- och sjukvårdsaktivitet' : 'er'}

    translator = Xlator(term_def_dict)
    
    # loop through each definition in the begrepp_dict_list and make one string with all the
    # definitions separated by the ' ½ ' string. Without the spaces, certain instances of words
    # are not detected at the boundaries. Send this string to the Xlator instantiation, and replace all 
    # the occurrences of begrepp in definitions with a hover tooltip text.

    joined_definitions = ' ½ '.join([i.get('definition') for i in begrepp_dict_list])
    joined_definitions_minus_nbsp = nbsp2space(joined_definitions)
    # only here are the regex patterns created in Xlator, couple to the substitution 
    altered_strings = translator.xlat(joined_definitions_minus_nbsp)
    # resplit the now altered string back into a list
    resplit_altered_strings = altered_strings.split(' ½ ')
    
    for index, begrepp in enumerate(begrepp_dict_list):
        try:
           begrepp_dict_list[index]['definition'] = format_html(resplit_altered_strings[index])
        except re.error as e:
           print(e)

    return begrepp_dict_list

def hämta_data_till_begrepp_view(url_parameter):
    search_request = retur_general_sök(url_parameter)

    begrepp = extract_columns_from_query_and_return_set(search_result=search_request, start=0, stop=5)
    synonym = extract_columns_from_query_and_return_set(search_result=search_request, start=5, stop=8)
    
    begrepp_column_names = ['begrepp_id', 'definition', 'term', 'utländsk_term', 'begrepp_status']

    return_list_dict = []
    for return_result in begrepp:
        return_list_dict.append(dict(zip(begrepp_column_names, return_result)))

    synonym_column_names = ['begrepp_id', 'synonym', 'synonym_status']

    return_synonym_list_dict = []
    for return_result in synonym:
        return_synonym_list_dict.append(dict(zip(synonym_column_names, return_result)))

    # this is all the terms and definitions from the DB
    term_def_dict = return_list_of_term_and_definition()
    
    return_list_dict = creating_tooltip_hover_with_definition_of_all_terms_present_in_search_result(begrepp_dict_list=return_list_dict,
                                             term_def_dict=term_def_dict)

    return_list_dict = highlight_search_term_i_definition(url_parameter, return_list_dict)
    
    return_list_dict = sort_returned_sql_search_according_to_search_term_position(return_list_dict, url_parameter)
    
    html = render_to_string(
        template_name="term-results-partial.html", context={'begrepp': return_list_dict,
                                                            'synonym' : return_synonym_list_dict,
                                                            'searched_for_term' : url_parameter}
                                                            
    )
    
    return html, return_list_dict


def begrepp_view(request):
    
    url_parameter = request.GET.get("q")
    
    #set_trace()
    if request.is_ajax():
        data_dict, return_list_dict = hämta_data_till_begrepp_view(url_parameter)        
        mäta_sök_träff(sök_term=url_parameter,sök_data=return_list_dict, request=request)
        return JsonResponse(data=data_dict, safe=False)

    # elif request.method == 'GET':
    #     data_dict, return_list_dict = hämta_data_till_begrepp_view(url_parameter)
    #     return render(request, "term-results-partial.html", context=data_dict)

    #elif request.method=='GET':
    #    return render(request, "term_forklaring_only.html", context=template_context)
    
    else:
        begrepp = Begrepp.objects.none()
    #    context = dict.fromkeys(['searched_for_term'], url_parameter)
    
    #context['begrepp'] = begrepp

    #print(f"context = {context}, {url_parameter}")
    
    return render(request, "term.html", context={'begrepp' : begrepp})

def begrepp_förklaring_view(request):

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
                               'källa',
                               'validated_by',
                               'term_i_system',
                               'externt_id',
                               'externt_register',
                               'status',
                               'term',
                               'utländsk_definition',
                               'utländsk_term',
                               'id_vgr',
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
        status_färg_dict = {'begrepp' :färg_status_dict.get(return_list_dict[0].get('status')),
                            'synonym' : färg_status_dict.get(return_synonym_list_dict[0].get('status'))}

        template_context = {'begrepp_full': return_list_dict[0],
                            'synonym_full' : return_synonym_list_dict,
                            'domän_full' : return_domän_list_dict,
                            'färg_status' : status_färg_dict}
        
        html = render_to_string(template_name="term_forklaring.html", context=template_context)
        
    # else:
    #     term_json = Begrepp.objects.none()

    if request.is_ajax():        
        return HttpResponse(html, content_type="html")

    elif request.method=='GET':
        if url_parameter is None:
            return render(request, "term.html", context={})
        else:
            return render(request, "term_forklaring_only.html", context=template_context)

    return render(request, "base.html", context={})

def hantera_request_term(request):
       
    if request.method == 'POST':
        
        type_of_request = request.get_raw_uri().split('?')[-1].split('=')


        if 'requestTranslate' in type_of_request:
            form = TermRequestTranslateForm(request.POST)
            if form.is_valid():

                ny_beställare = Bestallare()
                ny_beställare.beställare_email = form.clean_epost()
                ny_beställare.save()

                ny_term = Begrepp()
                ny_term.utländsk_term = form.clean_utländsk_term()
                ny_term.term = form.clean_begrepp()
                ny_term.begrepp_kontext = form.clean_kontext()
                ny_term.status = form.clean_status()
                ny_term.beställare = ny_beställare
                ny_term.save()

                inkommande_domän = Doman()
                if form.cleaned_data.get('other') == "Övrigt/Annan":
                    inkommande_domän.domän_namn = form.clean_not_previously_mentioned_in_workstream()
                else:
                    inkommande_domän.domän_namn = form.clean_workstream()
                inkommande_domän.save()


                return HttpResponse('''<div class="alert alert-success text-center" id="ajax_response_message">
                                    Tack! Begrepp skickades in för översättning.
                                    </div>''')

        else:
            form = TermRequestForm(request.POST, request.FILES)

            if form.is_valid():
            
                if request.FILES is not None:
                    file_list = []
                    for file in request.FILES.getlist('file_field'):
                        fs = FileSystemStorage()
                        filename = fs.save(content=file, name=file.name)
                        uploaded_file_url = fs.url(filename)
                        file_list.append(file.name)
                
                if Begrepp.objects.filter(term=request.POST.get('begrepp')).exists():
                        
                    return HttpResponse('''<div class="alert alert-danger text-center" id="ajax_response_message">
                                Begreppet ni önskade finns redan i systemet, var god och sök igen. :]
                                </div>''')
                else:

                    ny_beställare = Bestallare()
                    ny_beställare.beställare_namn = form.clean_name()
                    ny_beställare.beställare_email = form.clean_epost()
                    ny_beställare.beställare_telefon = form.clean_telefon()
                    ny_beställare.önskad_slutdatum = form.clean_önskad_datum()
                    ny_beställare.save()

                    ny_term = Begrepp()
                    ny_term.utländsk_term = form.clean_utländsk_term()
                    ny_term.term = form.clean_begrepp()
                    ny_term.begrepp_kontext = form.clean_kontext()
                    ny_term.beställare = ny_beställare
                    ny_term.save()
                    
                    inkommande_domän = Doman()
                    inkommande_domän.save()

                    if form.cleaned_data.get('other') == "Övrigt/Annan":
                        inkommande_domän.domän_namn = form.clean_not_previously_mentioned_in_workstream()
                    else:
                        inkommande_domän.domän_namn = form.clean_workstream()
                    
                    inkommande_domän.begrepp = ny_term

                    for filename in file_list:
                        new_file = BegreppExternalFiles()
                        new_file.begrepp = ny_term
                        new_file.support_file = filename
                        new_file.save()

                    return HttpResponse('''<div class="alert alert-success text-center" id="ajax_response_message">
                                    Tack! Begrepp skickades in för granskning.
                                    </div>''')

    elif request.is_ajax():
       #request.GET.get
        if 'translate' in request.GET.keys():
            form = TermRequestTranslateForm(initial={'utländsk_term' : request.GET.get("q")})
            
            return render(request, 'requestTerm.html', {'form': form, 
                                                        'whichTemplate' : 'requestTranslate',
                                                        'header' : 'Önskemål om ny översättning'})
        else:
            form = TermRequestForm(initial={'begrepp' : request.GET.get('q')})
        return render(request, 'requestTerm.html', {'form': form, 
                                                    'whichTemplate' : 'requestTerm',
                                                    'header' : 'Önskemål om nytt begrepp'})

    elif request.method == 'GET':
        return render(request, 'term.html', {})

def opponera_term(request):

    url_parameter = request.GET.get("q")
    
    if request.method == 'GET':
        inkommande_term = Begrepp(term=url_parameter)
        form = OpponeraTermForm(initial={'term' : inkommande_term})
        return render(request, 'opponera_term.html', {'opponera': form})

    elif request.method == 'POST':
        form = OpponeraTermForm(request.POST)
        if form.is_valid():
            
            opponera_term = OpponeraBegreppDefinition()
            opponera_term.begrepp_kontext = form.cleaned_data.get('resonemang')
            #opponera_term.datum = datetime.now().strftime("%Y-%m-%d %H:%M")
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

def return_number_of_recent_comments(request):
    
    if request.method == 'GET':
        total_comments = OpponeraBegreppDefinition.objects.all()
        status_list = [i.get('status') for i in total_comments.values()]
        return JsonResponse({'unreadcomments' : len(status_list)-status_list.count("Beslutad"),
                             'totalcomments' : len(status_list)})

def whatDoYouWant(request):

    url_parameter = request.GET.get("q")
    #set_trace()
    if request.method == 'GET':
        
         return render(request, "whatDoYouWant.html", context={'searched_for_term' : url_parameter})    
     # return render(request, "term.html", context={'begrepp' : begrepp})
 
