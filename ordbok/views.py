import json
from pdb import set_trace
from urllib.parse import unquote
from django.forms.models import model_to_dict
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from datetime import datetime
from django.db import connection, transaction
from django.db.models import Q
from django.core.mail import EmailMessage
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from django.urls import reverse, get_script_prefix

from django.utils.safestring import mark_safe
from begrepptjanst.settings.production import EMAIL_HOST_PASSWORD

from ordbok.models import *
from ordbok import models
from .forms import TermRequestForm, KommenteraTermForm
from .functions import mäta_sök_träff, mäta_förklaring_träff, Xlator, nbsp2space, HTML_TAGS, sort_begrepp_keys

import re
import logging
from begrepptjanst.logs import setup_logging
from django.utils.html import format_html
from django.views.generic import ListView

from django.core.paginator import Paginator

from django.core.mail import send_mail

logger = logging.getLogger(__name__)

re_pattern = re.compile(r'\s+')

färg_status_dict = {'Avråds' : 'table-danger',
                    'Avställd' : 'table-danger',
                    'Beslutad': 'table-success',
                    'Pågår': 'table-warning',
                    'Preliminär': 'table-warning',
                    'För validering': 'table-warning',
                    'Internremiss': 'table-warning',
                    'Ej Påbörjad': 'table-warning',
                    'Definiera ej': 'table-success',
                    'Publiceras ej' : 'table-light-blue'}

def retur_general_sök(url_parameter):

    queryset = Begrepp.objects.all().exclude(
                         status='Publicera ej'
                     ).filter(
                     Q(id__contains=url_parameter) |
                     Q(term__icontains=url_parameter) |
                     Q(anmärkningar__icontains=url_parameter) |
                     Q(definition__icontains=url_parameter) |
                     Q(utländsk_term__icontains=url_parameter) |
                     Q(synonym__synonym__icontains=url_parameter)
                     ).distinct()

    return queryset

def filter_by_first_letter(letter):

    queryset = Begrepp.objects.filter(
        ~Q(status="Publicera ej")).filter(
            term__istartswith=letter).values_list(
                'id',\
                'definition',\
                'term',\
                'utländsk_term',\
                'status',\
                'synonym__begrepp_id',\
                'synonym__synonym',\
                'synonym__synonym_status')
    return queryset

def retur_komplett_förklaring_custom_sql(url_parameter):

    return Begrepp.objects.get(pk=url_parameter)


def sort_returned_sql_search_according_to_search_term_position(lines, delim, position=1):
    
    '''
    Returns a sorted list based on "column" from list-of-dictionaries data.
    '''

    return sorted(lines, key=lambda x: x.get('term').lower().split(delim))


def highlight_search_term_i_definition(search_term, begrepp_dict_list):

    for idx, begrepp in enumerate(begrepp_dict_list):
        begrepp_dict_list[idx]['definition'] = begrepp.get('definition').replace(search_term, f'<mark>{search_term}</mark>')
        
    return begrepp_dict_list


def return_list_of_term_and_definition():
    
    result = Begrepp.objects.all().exclude(status='Publicera ej').values('term','definition')

    return result

def clean_dict_of_extra_characters(incoming_dict):

    clean_dict = {}
    for keys,values in incoming_dict.items():
        clean_dict[keys.strip()] = re.sub('\xa0', ' ', values)
    return clean_dict

def concatentate_all_dictionary_values_to_single_string(dictionary : dict, key : str):

    return ' ½ '.join([i.get(key) for i in dictionary])


def creating_tooltip_hover_with_definition_of_all_terms_present_in_search_result(begrepp_dict_list, term_def_dict):

    #create a set as there are duplicates in the database
    #term_def_set = set([(record.get('term'),record.get('definition')) for record in term_def_dict])
    # create a dictionary with the term as key and definition containing the HTML needed to show the hover definition

    term_def_dict_uncleaned = {
        record.get('term'):f'''<div class="definitiontooltip">{record.get('term').strip()}<div class="definitiontooltiptext">{record.get('definition')}</div></div>&nbsp;''' for record in term_def_dict
        }

    #term_def_dict_uncleaned = {}

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

    joined_definitions = concatentate_all_dictionary_values_to_single_string(begrepp_dict_list, 'definition')
    joined_definitions_minus_nbsp = nbsp2space(joined_definitions)
    gt_brackets, lt_brackets = find_all_angular_brackets(joined_definitions_minus_nbsp)
    
    joined_definitions_minus_nbsp = replace_non_html_brackets(joined_definitions_minus_nbsp, gt_brackets, lt_brackets)    
    logger.info(f'joined_definitions_minus_nbsp - {joined_definitions_minus_nbsp}')

    # only here are the regex patterns created in Xlator, couple to the substitution 
    altered_strings = translator.xlat(joined_definitions_minus_nbsp)
    # resplit the now altered string back into a list
    resplit_altered_strings = altered_strings.split(' ½ ')

    #begrepp_list = {}
    for index, begrepp in enumerate(begrepp_dict_list):
        try:
           begrepp_dict_list[index]['definition'] = resplit_altered_strings[index]
        except (re.error, KeyError) as e:
           print(e)

    return begrepp_dict_list

def find_all_angular_brackets(bracket_string):

    lt_brackets = []
    gt_brackets = []
    bracket_matches = [find for find in re.finditer(r'(?<=<).*?(?=>)', bracket_string)]
    for match in bracket_matches:
        if match.group(0) in HTML_TAGS:
            continue
        else:
            lt_brackets.append(match.start()-1)
            gt_brackets.append(match.end()+1)
    
    return gt_brackets, lt_brackets

def replace_str_index(text,index, index_shifter, replacement):

    return f"{text[:index+index_shifter]}{replacement}{text[index+1+index_shifter:]}"

def replace_non_html_brackets(edit_string, gt_brackets, lt_brackets):

    position_shifter = 0
    logger.info(f'unedited string - {edit_string}')
    logger.info(f'lt_brackets - {lt_brackets}')
    for lt_position in lt_brackets:
        edit_string = replace_str_index(edit_string, lt_position, position_shifter, '&lt;')
        logging.info(f'edited_string - {edit_string}')
        position_shifter += 3
    
    logger.info(f'gt_brackets before index change - {gt_brackets}')
    
    stepped_range = [i*3-1 for i in range(1, 4)]
    logger.info(f'stepped_range - {stepped_range}')
    zipped_lists = zip(stepped_range, gt_brackets)
    adjusted_gt_indexes = [x + y for (x, y) in zipped_lists]
    
    logger.info(f'gt_brackets after index change - {adjusted_gt_indexes}')
    logger.info('replacing > brackets')
    position_shifter=0
    for gt_position in adjusted_gt_indexes:        
        edit_string = replace_str_index(edit_string, gt_position, position_shifter, '&#62;')
        logging.info(f'edited_string - {edit_string}')
        position_shifter += 4

    return edit_string

def mark_fields_as_safe_html(list_of_dict, fields):


    for index, item in enumerate(list_of_dict):
        for field in fields:
            list_of_dict[index][field] = format_html(item.get(field))

    return list_of_dict

def hämta_data_till_begrepp_view(url_parameter):

    if (len(url_parameter) == 1) and (url_parameter.isupper()):
        search_request = filter_by_first_letter(letter=url_parameter)
        highlight=False
    else: 
        search_request = retur_general_sök(url_parameter)
        logger.info(f'len of search result = {len(search_request)}')

        highlight=True

    # this is all the terms and definitions from the DB
    all_terms_and_definitions_dict = return_list_of_term_and_definition()
    
    return_list_dict = creating_tooltip_hover_with_definition_of_all_terms_present_in_search_result(
        begrepp_dict_list = search_request.values(),
        term_def_dict = all_terms_and_definitions_dict
        )

    if highlight==True:
        return_list_dict = highlight_search_term_i_definition(
            url_parameter, 
            return_list_dict
            )
    
    return_list_dict = sort_returned_sql_search_according_to_search_term_position(
        return_list_dict, 
        url_parameter
        )

    return_list_dict = mark_fields_as_safe_html(return_list_dict, ['definition',])

    html = render_to_string(
        template_name="term-results-partial.html", context={'begrepp': return_list_dict,
                                                            'färg_status' : färg_status_dict,
                                                            'queryset' : search_request,
                                                            'searched_for_term' : url_parameter
                                                            }
                            )
    
    return html, return_list_dict

def begrepp_view(request):
    
    url_parameter = request.GET.get("q")
    
    if request.is_ajax():
        data_dict, return_list_dict = hämta_data_till_begrepp_view(url_parameter)

        mäta_sök_träff(sök_term=url_parameter,sök_data=return_list_dict, request=request)
        return JsonResponse(data=data_dict, safe=False)

    else:
        begrepp = Begrepp.objects.none()
    
    return render(request, "term.html", context={'begrepp' : begrepp})

def begrepp_förklaring_view(request):

    url_parameter = request.GET.get("q")
    
    if url_parameter:
        single_term = retur_komplett_förklaring_custom_sql(url_parameter)

        mäta_förklaring_träff(sök_term=url_parameter, request=request)

        status_färg_dict = {'begrepp' : färg_status_dict.get(single_term.status),
                            'synonym' : [[i.synonym,i.synonym_status] for i in single_term.synonym_set.all()]}
        
        template_context = {'begrepp_full': single_term,
                            'färg_status' : status_färg_dict}

        html = render_to_string(template_name="term_forklaring.html", context=template_context)

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

        form = TermRequestForm(request.POST, request.FILES)
    
        if form.is_valid():

            file_list = []
            if len(request.FILES) != 0:
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

                if form.cleaned_data.get('workstream') == "Övrigt/Annan":
                    ny_domän = form.clean_not_previously_mentioned_in_workstream()
                    if (ny_domän is not None) and (ny_domän != ''):
                        inkommande_domän.domän_namn = ny_domän
                        inkommande_domän.begrepp = ny_term
                        inkommande_domän.save()
                elif form.cleaned_data.get('workstream') == 'Inte relevant':
                    pass
                else:
                    inkommande_domän.domän_namn = form.clean_workstream()
                    inkommande_domän.begrepp = ny_term
                    inkommande_domän.save()

                for filename in file_list:
                    new_file = BegreppExternalFiles()
                    new_file.begrepp = ny_term
                    new_file.support_file = filename
                    new_file.save()

                return HttpResponse('''<div class="alert alert-success text-center" id="ajax_response_message">
                                Tack! Begrepp skickades in för granskning.
                                </div>''')
        else:
            
            return render(request, 'requestTerm.html', {'form': form,
                                                        'whichTemplate' : 'requestTerm'}, 
                                                        status=500)

    elif request.is_ajax():
       
        form = TermRequestForm(initial={'begrepp' : request.GET.get('q')})
        
        return render(request, 'requestTerm.html', {'form': form, 
                                                    'whichTemplate' : 'requestTerm',
                                                    'header' : 'Önskemål om nytt begrepp'})

    else:
        return render(request, 'term.html', {})

def kommentera_term(request):

    url_parameter = request.GET.get("q")
    
    if request.method == 'GET':
        inkommande_term = Begrepp(term=url_parameter)
        form = KommenteraTermForm(initial={'term' : inkommande_term})
        return render(request, 'kommentera_term.html', {'kommentera': form})

    elif request.method == 'POST':
        form = KommenteraTermForm(request.POST)
        if form.is_valid():
            file_list = []
            if len(request.FILES) != 0:
                for file in request.FILES.getlist('file_field'):
                    fs = FileSystemStorage()
                    filename = fs.save(content=file, name=file.name)
                    uploaded_file_url = fs.url(filename)
                    file_list.append(file.name)

            kommentera_term = KommenteraBegreppDefinition()
            kommentera_term.begrepp_kontext = form.cleaned_data.get('resonemang')
            kommentera_term.epost = form.cleaned_data.get('epost')
            kommentera_term.namn = form.cleaned_data.get('namn')
            kommentera_term.status = models.DEFAULT_STATUS
            kommentera_term.telefon = form.cleaned_data.get('telefon')
            # entries with doublets cause a problem, so we take the first one
            kommentera_term.begrepp = Begrepp.objects.filter(term=form.cleaned_data.get('term')).first()
            kommentera_term.save()

            for filename in file_list:
                new_file = BegreppExternalFiles()
                new_file.begrepp = kommentera_term.begrepp
                new_file.kommentar = kommentera_term
                new_file.support_file = filename
                new_file.save()

            return HttpResponse('''<div class="alert alert-success">
                                   Tack för dina synpunkter.
                                   </div>''')

def prenumera_till_epost(request):

    if request.method == 'GET':
        epost = request.GET.get('epost')

        send_mail(
            'Prenumera till beslutade begrepp utskick',
            f'Hej! {epost} vill prenumera mig till den veckovis utskicket av beslutade begrepp från Informatik och standardisering.',
            epost,
            ['informatik@vgregion.se'],
            fail_silently=False,
            auth_user=settings.EMAIL_HOST_USER,
            auth_password=settings.EMAIL_HOST_PASSWORD
        )

    return HttpResponseRedirect(get_script_prefix())


def return_number_of_recent_comments(request):
    
    if request.method == 'GET':
        total_comments = KommenteraBegreppDefinition.objects.all()
        status_list = [i.get('status') for i in total_comments.values()]
        return JsonResponse({'unreadcomments' : len(status_list)-status_list.count("Beslutad"),
                             'totalcomments' : len(status_list)})

def whatDoYouWant(request):

    url_parameter = request.GET.get("q")
    if request.method == 'GET':
        
         return render(request, "whatDoYouWant.html", context={'searched_for_term' : url_parameter})    
 
def autocomplete_suggestions(request, attribute, search_term):

    logger = logging.getLogger(__name__)

    logger.debug(f'incoming autocomplete - {attribute}, {search_term}')
    attribute = unquote(attribute)
    logger.debug(f'unquote special characters - {attribute}, {search_term}')
    custom_filter = {}
    custom_filter[attribute+'__icontains'] = search_term

    queryset = Begrepp.objects.filter(**custom_filter)
    
    suggestion_dict = {}
    
    if not queryset:
        suggestions = ['']
    else:
        for entry in queryset:
            if suggestion_dict.get(attribute) is None:
                suggestion_dict[attribute] = [getattr(entry, attribute)]
            else:
                suggestion_dict[attribute].append(getattr(entry, attribute))

        suggestions = suggestion_dict.values()
        
        suggestions = list(set([i for i in suggestions][0]))
        
        suggestions = sorted(suggestions, key=len)[0:6]

    return JsonResponse(suggestions, safe=False)


def all_non_beslutade_begrepp(request):

    queryset = Begrepp.objects.all().filter(~Q(status='Beslutad') & 
                                            ~Q(status__icontains='översättning') & 
                                            ~Q(status__icontains='publicera ej')).prefetch_related().values()


    return JsonResponse(list(queryset), json_dumps_params={'ensure_ascii':False}, safe=False)

def all_beslutade_terms(request):

    queryset = Begrepp.objects.all().filter(~Q(status__icontains='översättning') & 
                                            ~Q(status__icontains='publicera ej')).prefetch_related().values()
    
    return JsonResponse(list(queryset), json_dumps_params={'ensure_ascii':False}, safe=False)


from django.core import serializers

def get_term(request, id):

    logger.info(f'Getting begrepp {id}')
    queryset = Begrepp.objects.filter(pk=id).values()

    return JsonResponse(list(queryset), json_dumps_params={'ensure_ascii':False}, safe=False)


def all_synonyms(request):
        querylist = list(Synonym.objects.all().values())
        return JsonResponse(querylist, json_dumps_params={'ensure_ascii':False}, safe=False)

def all_översättningar(request):
        querylist = list(Begrepp.objects.filter(status='Översättning').values())
        return JsonResponse(querylist, json_dumps_params={'ensure_ascii':False}, safe=False)

