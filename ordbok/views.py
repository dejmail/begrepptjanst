import json
import logging
import re
from datetime import datetime
from pdb import set_trace
from urllib.parse import unquote

from begrepptjanst.logs import setup_logging
from begrepptjanst.settings.production import EMAIL_HOST_PASSWORD
from ordbok.models import DEFAULT_STATUS
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.core.mail import EmailMessage, send_mail
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator
from django.db import connection, transaction
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.forms.models import model_to_dict
from django.http import (
    HttpRequest, 
    HttpResponse, 
    HttpResponseRedirect, 
    JsonResponse
)
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.urls import get_script_prefix, reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.views.generic import ListView
from django.db.models import QuerySet
from typing import List, Dict




from ordbok.forms import KommenteraTermForm, TermRequestForm
from ordbok.functions import (HTML_TAGS, Xlator, mäta_förklaring_träff,
                              mäta_sök_träff, replace_nbs_with_normal_space, sort_begrepp_keys)
from ordbok.models import (Begrepp, BegreppExternalFiles, Bestallare,
                           Dictionary, KommenteraBegrepp, Synonym)

logger = logging.getLogger(__name__)

re_pattern = re.compile(r'\s+')

COLOUR_STATUS_DICT = {'Avråds' : 'table-danger',
                    'Avställd' : 'table-danger',
                    'Beslutad': 'table-success',
                    'Pågår': 'table-warning',
                    'Preliminär': 'table-warning',
                    'För validering': 'table-warning',
                    'Internremiss': 'table-warning',
                    'Ej Påbörjad': 'table-warning',
                    'Definiera ej': 'table-success',
                    'Publiceras ej' : 'table-light-blue'}

def retur_general_sök(url_parameter, dictionary):

    """ Check whether the  :model:`ordbok.Begrepp` contains entries in the 
    attributes specified.
    
    Arguments: 
    url_parameter {str} -- Search string sent by the user
    :return: A queryset of matches
    :rtype: Queryset
        
    """

    queryset = Begrepp.objects.exclude(status='Publicera ej').filter(
        Q(id__contains=url_parameter) |
        Q(term__icontains=url_parameter) |
        Q(anmärkningar__icontains=url_parameter) |
        Q(definition__icontains=url_parameter) |
        Q(utländsk_term__icontains=url_parameter) |
        Q(synonym__synonym__icontains=url_parameter)
    ).distinct()    
    
    return queryset.filter(dictionaries__dictionary_name=dictionary)
    
def filter_by_first_letter(letter, dictionary):

    """ A filter of :model:`ordbok.Begrepp` which returns a queryset 
    where the terms start with a certain letter.
    
    Arguments: 
    letter {str} -- String letter to filter with
    :return: A queryset of matches
    :rtype: Queryset
        
    """ 

    queryset = Begrepp.objects.filter(
        ~Q(status="Publicera ej")
        ).filter(
        term__istartswith=letter
        ).distinct()
    
    return queryset.filter(dictionaries__dictionary_name=dictionary)

def filter_by_dictionary(queryset: QuerySet, dictionary: List) -> QuerySet:
    """
    Filters a queryset of Begrepp objects by the specified Dictionary.

    Args:
        queryset (QuerySet): The queryset to filter.
        dictionary (Dictionary): The dictionary to filter by.

    Returns:
        QuerySet: The filtered queryset.
    """

    logger.info(f'Filtering search frontend query by {dictionary}')

    return queryset.filter(dictionaries__dictionary_name=dictionary)

def determine_search_strategy(url_parameter, dictionary):

    if len(url_parameter) == 1 and url_parameter.isupper():
        logger.info(f'Searching by single letter - {url_parameter}')
        return filter_by_first_letter(letter=url_parameter, dictionary=dictionary), False
    else:
        logger.info(f'Searching by entered term - {url_parameter}')
        return retur_general_sök(url_parameter, dictionary=dictionary), True

def return_single_term_by_id(id: int) -> Begrepp:

    """Return a single match of :model:`ordbok.Begrepp`

    Arguments: 
    id {str} -- ID of the match requested by the user
    :return: A queryset match
    :rtype: Begrepp

    >>>return_single_term_by_id(1) #doctest: +ELLIPSIS
    [<Begrepp: doctest_unpredicatable.Begrepp>]

    """
    try:
        return Begrepp.objects.get(pk=id)
    except ObjectDoesNotExist:
        return 'No concept of this Id exists'

def filter_term_by_string(term: str) -> QuerySet[Begrepp]:

    """Return a filter list of :model:`ordbok.Begrepp`

    Arguments: 
    term {str} -- string of the match requested by the user
    :return: A queryset match
    :rtype: Queryset

    >>>filter_term_by_string(1) #doctest: +ELLIPSIS
    [<Begrepp: doctest_unpredicatable.Begrepp>]

    """

    return Begrepp.objects.filter(term=term)

def sort_results_according_to_search_term(queryset: QuerySet[Begrepp], 
                                          url_parameter: str, position: 
                                          int = 1) -> QuerySet[Begrepp]:
    
    """Returns a sorted list based on "column" from list-of-dictionaries data.

    Arguments: 
    queryset {queryset} -- queryset containing terms to be returned to the UI
    url_parameter {str} -- The str with which to split each term with
    :return: Sorted list
    :rtype: list
    """
    
    return sorted(queryset, key=lambda x: x.get('term').lower().split(url_parameter))


def highlight_search_term_i_definition(search_term : str, 
                                       begrepp_dict_list: QuerySet[Dict[str, str]]
                                       ) -> Dict:

    """Encapsulate the search string with HTML <mark> tag in the definition of 
    the term.

    Arguments: 
    search_term {str} -- the string which should be encased in HTML <mark>
    begrepp_dict_list -- class of type Queryset
    :return: A list of dictionaries
    :rtype: class of type Queryset
    """

    # for idx, begrepp in enumerate(begrepp_dict_list):
    #     set_trace()
    #     begrepp_dict_list[idx]['definition'] = begrepp.get('definition').replace(search_term, f'<mark>{search_term}</mark>')
        
    # return begrepp_dict_list

    # Pattern to match <span> tags that contain the search term
    span_pattern = re.compile(
        rf"(<span[^>]*>[^<]*?{re.escape(search_term)}[^<]*?</span>)", 
        re.IGNORECASE | re.DOTALL
    )

    def wrap_with_mark(match):
        """Wrap <mark> around the entire <span> tag found."""
        return f'<mark>{match.group(0)}</mark>'

    for idx, begrepp in enumerate(begrepp_dict_list):
        definition = begrepp.get('definition', '')

        # Wrap <mark> around <span> elements that contain the search term
        definition = span_pattern.sub(wrap_with_mark, definition)

        begrepp_dict_list[idx]['definition'] = definition

    return begrepp_dict_list


def return_list_of_term_and_definition(dictionary: str) -> QuerySet[Begrepp]:
    
    
    """Return values "term" and "definition" from a queryset of all terms in
     :model:`ordbok.Begrepp`.

    Arguments: 
    :return: A queryset of dictionaries all terms excluding those with status 'Publicer ej'
    :rtype: class of type Queryset
    """

    queryset = Begrepp.objects.all().exclude(status='Publicera ej').values('term','definition')
    queryset = filter_by_dictionary(queryset, dictionary)

    return queryset

def clean_dict_of_extra_characters(incoming_dict: dict) -> dict:

    """ Using regular expression, replace all \xa0 characters that are present
    in the definition strings.

    Arguments:
    incoming_dict {dict} -- A dictionary of with key:value as term:definition
    
    :return: A dictionary
    :rtype: dict
    """

    clean_dict = {}
    for keys,values in incoming_dict.items():
        clean_dict[keys.strip()] = re.sub('\xa0', ' ', values)

    logger.debug(f"After stripping and subst - patient : {clean_dict.get('patient')}")
    return clean_dict

def concatenate_all_dictionary_values_to_single_string(dictionary: Dict, 
                                                       key: str = 'definition') -> str:

    """ 
        Concatenate all the values of the given key from a nested dictionary 
        into a single string with a spacer.

    Args:
        dictionary (Dict[str, Dict[str, str]]): A dictionary where each value 
        is another dictionary. 
        key (str): The key to extract the value from each inner dictionary. 
        Default is 'definition'.

    Returns:
        str: A single string created by joining all the values of the given key
        with a spacer.
    """

    definitions_list = []
    for entry in dictionary:        
        if not entry.get('definition').strip():  # Check if the value is empty or contains only whitespace
            logger.debug(f"Warning: The definition for key '{key}' is empty or contains only whitespace.")
        definitions_list.append(entry.get('definition', 'Ingen definition'))

    concatenated_text = ' ½ '.join(definitions_list)
    
    # Regular expression to check for multiple consecutive ' ½ ' strings
    if re.search(r'( ½ ){2,}', concatenated_text):
        logger.debug("The string contains multiple consecutive ' ½ ' separators.")
    else:
        logger.debug("No multiple consecutive ' ½ ' separators found.")

    return concatenated_text

def creating_tooltip_hover_substitution_object(all_terms_and_definitions : QuerySet):

    """ Manipulate an incoming dictionary that has a 'term' and 'definition'
     key:value so that when a definition has references to other term/s
     within :model:`ordbok.Begrepp`, those references have a tooltip 
     connected show the definition on the UI.
     
     Arguments: 
    search_results {dict} -- A list of key:values of the search results
    all_terms_and_definitions [{}] -- A list of dictionaries of all term:definitions within :model:`ordbok.Begrepp`

    :return: A dictionary where the 'key' has been altered
    :rtype:
    """
        
    terms_with_tooltips = {
        record.get('term'):f'''
        <span class="term" 
              tabindex="0" 
              role="button" 
              aria-describedby="def-{record.get('term').strip()}">{record.get('term').strip()}</span>
        <div id="def-{record.get('term').strip()}" class="tooltiptext" hidden>{record.get('definition')}</div>

        ''' for record in all_terms_and_definitions}
    
    logger.debug(f'Number of records in {len(terms_with_tooltips)=}') 
    logger.debug(f"After tooltip adding - (patient, {terms_with_tooltips.get('patient')}")
    
    clean_terms_with_tooltips = clean_dict_of_extra_characters(terms_with_tooltips)
    
    logger.debug(f"After cleaning tooltip of extra chars - (patient, {clean_terms_with_tooltips.get('patient')}")
    
    # Would be good to be able to send a list of plurals that we could 
    # group togther in the pattern creation, but as Xlator is a dict
    # class, I'm not sure how to accomplish that.

    xlator_instance = Xlator(clean_terms_with_tooltips)

    return xlator_instance
    
    # loop through each definition in the begrepp_dict_list and make one string with all the
    # definitions separated by the ' ½ ' string. Without the spaces, certain instances of words
    # are not detected at the boundaries. Send this string to the Xlator instantiation, and replace all 
    # the occurrences of begrepp in definitions with a hover tooltip text.

def substitute_occurrence_of_terms_in_definitions(search_results, xlator_instance, key):

    joined_definitions = concatenate_all_dictionary_values_to_single_string(search_results, key)

    joined_definitions_minus_nbsp = replace_nbs_with_normal_space(joined_definitions)
    gt_brackets, lt_brackets = find_all_angular_brackets(joined_definitions_minus_nbsp)
    
    joined_definitions_minus_nbsp = replace_non_html_brackets(joined_definitions_minus_nbsp, gt_brackets, lt_brackets)    
    
    # only here are the regex patterns created in Xlator, couple to the substitution 
    altered_strings = xlator_instance.xlat(joined_definitions_minus_nbsp)
    # resplit the now altered string back into a list
    resplit_altered_strings = altered_strings.split(' ½ ')

    logger.debug(f'Length of {len(resplit_altered_strings)=}')

    log_output = [(i.get('term'), i.get('definition')) for i in search_results if i.get('term') == 'patient']
    logger.debug(f"After replacing brackets, spaces {log_output}")    
    
    for index, begrepp in enumerate(search_results):
        try:
           #set_trace()
           search_results[index][key] = resplit_altered_strings[index]
        except (re.error, KeyError) as e:
           print(e) 
    
    return search_results

def find_all_angular_brackets(bracket_string):

    """ Definitions of terms often include < > brackets within the definitions which
    are interpreted as HTML which confused the template engine. This function finds
    all the < > that do not enclose a standard HTML tag.

    :return: two lists containing the positions of either < or >
    :rtype: list
    """

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

    """ Return a string where string formatting was used to replace a 
    certain character at a certain index with a different string.

    Arguments:
    text {str} -- The string from which the indices are calculated 
    index {int} -- An index of interest
    index_shifter {int} -- How much the original index needs to be shifted by
    replacement {str} -- The replacement string

    :return: a string with a bracket replaced with HTML character for < or >
    :rtype: str
    """

    return f"{text[:index+index_shifter]}{replacement}{text[index+1+index_shifter:]}"

def replace_non_html_brackets(edit_string, gt_brackets, lt_brackets):

    """ Iterate through a string and replace the < and > characters with the 
    corresponding HTML equivalent.
    
    Arguments:
    edit_string {str} -- String containing <> that are not HTML
    gt_brackets {list} -- String positions representing greater than character
    lt_brackets {list} -- String positions representing lesser than character
    :return: string with non-html < > characters
    :rtype: str
    """

    index_shifter = 0
    # logger.debug(f'unedited string - {edit_string}')
    # logger.debug(f'lt_brackets - {lt_brackets}')
    for lt_position in lt_brackets:
        edit_string = replace_str_index(edit_string, lt_position, index_shifter, '&lt;')
        #logging.debug(f'edited_string - {edit_string}')
        index_shifter += 3
    
    # logger.info(f'gt_brackets before index change - {gt_brackets}')
    
    stepped_range = [i*3-1 for i in range(1, 4)]
    # logger.debug(f'stepped_range - {stepped_range}')
    zipped_lists = zip(stepped_range, gt_brackets)
    adjusted_gt_indexes = [x + y for (x, y) in zipped_lists]
    
    # logger.debug(f'gt_brackets after index change - {adjusted_gt_indexes}')
    # logger.debug('replacing > brackets')
    index_shifter=0
    for gt_position in adjusted_gt_indexes:        
        edit_string = replace_str_index(edit_string, gt_position, index_shifter, '&#62;')
        # logging.debug(f'edited_string - {edit_string}')
        index_shifter += 4

    return edit_string

def mark_fields_as_safe_html(list_of_dict, fields):

    """ Make certain fields within a list of dictionary
    objects as safe html

    Arguments:
    list_of_dict {list} -- A list of dictionary objects containing term search results
    fields {list} -- A list of fields to make HTML safe
    :return: A list of dictionary objects where supplied key values are HTML safe
    :rtype: list
    """
    
    for index, item in enumerate(list_of_dict):
        for field in fields:
            list_of_dict[index][field] = format_html(item.get(field))

    return list_of_dict

def is_ajax(request: HttpRequest) -> HttpResponse:
    
    return request.headers.get('X-Custom-Requested-With')
        
def determine_search_strategy(url_parameter, dictionary):

    if len(url_parameter) == 1 and url_parameter.isupper():
        return filter_by_first_letter(letter=url_parameter, dictionary=dictionary), False
    else:
        return retur_general_sök(url_parameter, dictionary=dictionary), True

def assemble_search_results_view(url_parameter, dictionary):

    """
    Main method that couples together all the submethods needed to
    produce the HTML needed for the initial search view.

    Arguments:
        url_parameter {str} -- The search string sent by the user search
        domain {str} -- Subset of terms to filter the query with
    
    Returns:
        Tuple[str, dict]: A tuple containing the rendered HTML page with 
        the search results and the stylised results.
    
    """

    try:
        search_results, should_highlight = determine_search_strategy(url_parameter, dictionary)
        logger.debug(f'Searching within {dictionary=}')

        log_result = [(search_result.term, search_result.definition) for search_result in search_results if search_result.term=='patient']
        logger.debug(f"After general search - {log_result}")
    except Exception as e:
        logger.error(f"Error determing search strategy: {e}")
        return render_to_string("error-page.html", context={})

    # this is all the terms and definitions from this dictiomary in the DB
    all_terms_and_definitions = return_list_of_term_and_definition(dictionary)

    xlator_instance = creating_tooltip_hover_substitution_object(all_terms_and_definitions)

    styled_results = substitute_occurrence_of_terms_in_definitions(
        search_results = search_results.values(),
        xlator_instance=xlator_instance,
        key='definition'
        )
    
    log_result = [(i.get('term'),i.get('definition')) for i in styled_results if i.get('term')=='patient']
    logger.debug(f'After creating tooltip {log_result}')

    if should_highlight:
        styled_results = highlight_search_term_i_definition(
            url_parameter, 
            styled_results
            )
    
    styled_results = sort_results_according_to_search_term(
        styled_results, 
        url_parameter
        )

    styled_results = mark_fields_as_safe_html(styled_results, ['definition',])

    html = render_to_string(
        template_name="term_results_partial.html", 
        context={'styled_results': styled_results,
        'colour_status' : COLOUR_STATUS_DICT,
        'search_results' : search_results,
        'searched_for_term' : url_parameter,
        'chosen_dictionary' : Dictionary.objects.get(dictionary_name=dictionary).dictionary_name
        }
        )    

    return html, styled_results

def main_search_view(request):

    """ The view that processes the initial search from the user

    Arguments:
    request -- Incoming requrest object from the browser
    :return: HttpResponse object containing template and context
    :rtype: HttpResponse
    """
    url_parameter = request.GET.get("q")
    dictionary = request.GET.get("dictionary")
    if is_ajax(request):
        
        data_dict, styled_results = assemble_search_results_view(url_parameter, dictionary)
    
        mäta_sök_träff(sök_term=url_parameter,sök_data=styled_results, request=request)
        return JsonResponse(data=data_dict, safe=False)

    else:
        logger.debug("Search not ajax, or no search term")
        begrepp = Begrepp.objects.none()
    
    html = render_to_string('term.html', context={'begrepp' : begrepp})
    
    return render(request, "term.html", context={
        'dictionaries' : Dictionary.objects.all().order_by('order').values_list(
            'dictionary_name',
            'dictionary_long_name'
            ),
        'html' : html
        })

def term_metadata_view(request):

    """ View that processes the request for detailed information about a certain term

    Arguments:
    request: {HttpRequest} -- Request containing the id of the term of interest
    :return: HttpResponse object containing template and context of a single term
    :rtype: HttpResponse
    """

    url_parameter = request.GET.get("q")
    
    if url_parameter:
        single_term = return_single_term_by_id(url_parameter)

        mäta_förklaring_träff(sök_term=url_parameter, request=request)

        status_färg_dict = {'begrepp' : COLOUR_STATUS_DICT.get(single_term.status),
                            'synonym' : [[i.synonym,i.synonym_status] for i in single_term.synonym_set.all()]}
        
        template_context = {'begrepp_full': single_term,
                            'färg_status' : status_färg_dict}
        html = render_to_string(template_name="term_metadata_ajax.html", context=template_context)

        if is_ajax(request):        
            return JsonResponse(
                html, safe=False
                )

        elif request.method == 'GET':
            if url_parameter is None:
                return render(request, "term.html", context={})
            else:
                return render(request, "term_full_metadata.html", context=template_context)

    return render(request, "base.html", context={})

def handle_file_uploads(request_files):

    """ Generic function for handling file uploads

    Arguments:
    request: {HttpRequest} -- The file component a request.FILES object. The individual files
    if multiple will be saved and a list of filenames created
    :return:  A list of filenames
    :rtype: [List]

    """

    file_list = []
    for file in request_files.getlist('file_field'):
        fs = FileSystemStorage()
        filename = fs.save(content=file, name=file.name)
        uploaded_file_url = fs.url(filename)
        file_list.append(file.name)
    return file_list

def get_or_create_orderer(name, email):

    return Bestallare.objects.filter(
                    Q(beställare_namn__icontains=name) |
                    Q(beställare_email__icontains=email)
                )


def request_new_term(request):

    """ Send the form data when a user wants to request a new term or 
    manage the POST data if the user submits the request.

    Arguments:
    request: {HttpRequest} -- Request object containing the POST information that
    will be saved to db for processing. The POST information can include a file
    upload as well. If the user send in the form is already in the DB, and the
    contact details are the same, the first instance of that will be used.
    :return: A HttpResponse containing a Bootstrap alert is sent back
    :rtype: {HttpResponse}
    """
    
    if request.method == 'POST':

        form = TermRequestForm(request.POST, request.FILES)
        file_list = []
    
        if form.is_valid():

            if len(request.FILES) != 0:
                file_list = handle_file_uploads(request.FILES)                
            
            if filter_term_by_string(request.POST.get('begrepp')).exists():
                    
                return HttpResponse('''<div class="alert alert-danger text-center" id="ajax_response_message">
                            Begreppet ni önskade finns redan i systemet, var god och sök igen. :]
                            </div>''')
            else:

                existing_orderer = get_or_create_orderer(form.clean_name(),
                                                         form.clean_epost)

                if existing_orderer and len(existing_orderer) == 1:
                    new_ordered = existing_orderer
                else:
                    new_ordered = Bestallare()
                    new_ordered.beställare_namn = form.clean_name()
                    new_ordered.beställare_email = form.clean_epost()
                    new_ordered.beställare_telefon = form.clean_telefon()
                    new_ordered.save()

                new_term = Begrepp()
                new_term.utländsk_term = form.clean_utländsk_term()
                new_term.term = form.clean_begrepp()
                new_term.begrepp_kontext = form.clean_kontext()
                new_term.beställare = new_ordered
                new_term.save()

                # saving not necessary again
                new_term.dictionaries.set(form.clean_dictionary())

                for filename in file_list:
                    new_file = BegreppExternalFiles()
                    new_file.begrepp = new_term
                    new_file.support_file = filename
                    new_file.save()

                return HttpResponse('''<div class="alert alert-success text-center" id="ajax_response_message">
                                Tack! Begrepp skickades in för granskning.
                                </div>''')
        else:
            
            return render(request, 'request_new_term.html', {'form': form,
                                                        'whichTemplate' : 'requestTerm'}, 
                                                        status=500)
        
    elif is_ajax(request):
       
        form = TermRequestForm(initial={'begrepp' : request.GET.get('q'),
                                        'dictionary' : request.GET.get('dictionary')
                                        })
        
        return render(request, 'request_new_term.html', {'form': form, 
                                                    'whichTemplate' : 'requestTerm',
                                                    'header' : 'Önskemål om nytt begrepp'})

    else:
        return render(request, 'term.html', {})

def kommentera_term(request):

    """ Send back either the form to allow the submission of comments or
    process the submitted form and save the data to db.

    Arguments:
    request {HttpRequest} -- HttpRequest object containing the POST/GET data
    :return: HttpResponse with a Bootstrap alert response if form submitted via 
    POST and saved successfully, or an empty form via GET that can be filled out.
    :rtype: {HttpResponse}
    """
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

            kommentera_term = KommenteraBegrepp()
            kommentera_term.begrepp_kontext = form.cleaned_data.get('resonemang')
            kommentera_term.epost = form.cleaned_data.get('epost')
            kommentera_term.namn = form.cleaned_data.get('namn')
            kommentera_term.status = DEFAULT_STATUS
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

    """ A view that takes in a request containing an email address that is
    then emailed to the generic email address to be added to a subscription.

    :return: HttpResponseRedirect back to the base page
    :rtype: {HttpResponseRedirect} 
    """

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


@login_required
def return_number_of_comments(request):
    """ Returns JSON with total number of comments, and total number of unread comments
    based on a status of 'Beslutad', filtered by the logged-in user's groups and dictionaries.
    """
    if request.method == 'GET':
        # Get the logged-in user
        user = request.user

        # Get the groups the user belongs to
        user_groups = user.groups.all()

        # Find all Dictionary IDs associated with the user's groups
        dictionary_ids = Dictionary.objects.filter(groups__in=user_groups).values_list('dictionary_id', flat=True)

        # Find all Begrepp IDs associated with these Dictionary IDs
        begrepp_ids = Begrepp.objects.filter(dictionaries__dictionary_id__in=dictionary_ids).values_list('id', flat=True)

        # Filter KommenteraBegrepp based on the filtered Begrepp IDs
        total_comments = KommenteraBegrepp.objects.filter(begrepp__id__in=begrepp_ids)
        
        # Calculate unread comments
        unread_comments_count = total_comments.exclude(status="Beslutad").count()
        total_comments_count = total_comments.count()

        return JsonResponse({
            'unreadcomments': unread_comments_count,
            'totalcomments': total_comments_count
        })

def no_search_result(request):

    """ A view that was used to provide different choices based on what the user
    chose to do if the initial search had zero results.

    :return: A HttpResponse with HTML template and context
    :rtype: {HttpResponse}
    """

    url_parameter = request.GET.get("q")
    dictionary = request.GET.get("dictionary")
    if request.method == 'GET':
        
         return render(request, "no_search_result.html", context={'searched_for_term' : url_parameter,
                                                                  'chosen_dictionary' : dictionary})    
 
def autocomplete_suggestions(request, attribute, search_term):
    """
    Provides autocomplete suggestions for a given attribute based on user input.

    Args:
        request (HttpRequest): The incoming HTTP request.
        attribute (str): The attribute in the database to search.
        search_term (str): The search term entered by the user.

    Returns:
        JsonResponse: A JSON response containing a list of matching suggestions.
    """
    logger = logging.getLogger(__name__)
    logger.debug(f'incoming autocomplete - {attribute}, {search_term}')

    attribute = unquote(attribute)
    logger.debug(f'unquote special characters - {attribute}, {search_term}')

    suggestions = get_autocomplete_suggestions(attribute, search_term)
    return JsonResponse(suggestions, safe=False)

def get_autocomplete_suggestions(attribute, search_term):
    """
    Retrieves a list of autocomplete suggestions from the database.

    Args:
        attribute (str): The attribute in the database to search.
        search_term (str): The search term entered by the user.

    Returns:
        list: A sorted 6 item list of unique suggestions.
    """

    if not search_term:
        return ['']

    custom_filter = {f"{attribute}__icontains": search_term}
    queryset = Begrepp.objects.filter(**custom_filter)

    if not queryset.exists():
        return ['']

     # Generate a list of tuples with (length, order, value)
    suggestions = [
        (len(getattr(entry, attribute)), i, getattr(entry, attribute))
        for i, entry in enumerate(queryset)
    ]

    # Sort by length first, then by original order
    suggestions.sort()

    # Extract just the value
    return [value for _, _, value in suggestions][:6]

def get_dictionary_data(request, dictionary):

    logger.info(f'Getting card text for {dictionary}')
    try:
        dictionary_instance = Dictionary.objects.get(dictionary_name=unquote(dictionary))
        # Convert to a dictionary and filter out non-field attributes
        data = {k: v for k, v in dictionary_instance.__dict__.items() if not k.startswith('_')}
        
        return JsonResponse(data)
    except Dictionary.DoesNotExist:
        logger.info(f'Requestion dictionary *{dictionary}* does not exist')
        return JsonResponse({'error': 'Dictionary not found'}, status=404)


def redirect_to_all_beslutade_terms(request):

    """ Returns a redirect response to all the terms that have been accepted.

    :return: HTTP Response redirect
    :rtype: {JsonResponse}
    """

    logger.info('Base url for terms hit, keyword "all" not supplied, redirecting')

    return HttpResponseRedirect(reverse('get_all_accepted_terms_as_json'))

def merge_term_and_synonym(qs, syn_qs):

    synonym_list = {
        "prohibited_synonyms" : [],
        "approved_synonyms" : []
                }
    if len(qs) == 1:

        for synonym in syn_qs:
            if synonym.get('synonym_status') == "Tillåten":
                synonym_list['approved_synonyms'].append(synonym.get('synonym'))
            elif synonym.get('synonym_status') == "Avråds":
                synonym_list['prohibited_synonyms'].append(synonym.get('synonym'))
    
        if qs[0].get('synonym') == None:
            qs[0]['synonyms'] = []
        qs[0]['synonyms'] = synonym_list

    elif len(qs) > 1:
        for id, record in qs.items():

            synonym_list = {
                "prohibited_synonyms" : [],
                "approved_synonyms" : []
                }

            synonyms = syn_qs.filter(begrepp_id=id)
            if synonyms and len(synonyms) > 0:
                for synonym in synonyms:
                    if synonym.get('synonym_status') == "Tillåten":
                        synonym_list['approved_synonyms'].append(synonym.get('synonym'))
                    elif synonym.get('synonym_status') == "Avråds":
                        synonym_list['prohibited_synonyms'].append(synonym.get('synonym'))
                qs[id]['synonyms'] = synonym_list        
            else:
                qs[id]['synonyms'] = synonym_list

    return qs

def all_accepted_terms(request):

    """ Returns a JSON list of all terms with status 'Publicera ej'

    :return: JSON list of term dictionaries
    :rtype: {JsonResponse}
    """

    queryset = Begrepp.objects.all().filter(
        ~Q(status__icontains='publicera ej'),
        ~Q(status__icontains='ej påbörjad'),
        ~Q(status__icontains='pågår'),
        ~Q(status__icontains='internremiss'),
        ).prefetch_related().values()
    
    
    qs_dict = {i.get('id'): i for i in queryset}

    synonym_qs = Synonym.objects.filter(
        begrepp_id__in=queryset.values_list(
        'id', flat=True)
        ).values()
    
    merged_result = merge_term_and_synonym(qs_dict, synonym_qs)
    
    merged_result = list(merged_result.values())

    return JsonResponse(merged_result, json_dumps_params={'ensure_ascii':False}, safe=False)


from django.core import serializers


def get_term(request, id):

    """ Obtain a single term from :model:`ordbok.Begrepp` and return a Queryset
    dictionary that is presented as JSON. 

    :return: JSON object of a single term
    :rtype: {JsonResponse}
    """

    logger.info(f'Getting begrepp {id}')
    queryset = Begrepp.objects.filter(pk=id).values()

    synonym_qs = Synonym.objects.filter(
        begrepp_id__in=queryset.values_list(
        'id', flat=True)
        ).values()
    
    merged_result = merge_term_and_synonym(queryset, synonym_qs)

    if queryset:
        return JsonResponse(list(merged_result), json_dumps_params={'ensure_ascii':False}, safe=False)
    else:
        return JsonResponse({'error' : 'No terms that match that id'})


def all_synonyms(request):

    """ Obtain all the synonyms from the :model:`ordbok.Synonym` and return
    a Queryset dictionary presented as JSON 

    :return: Json object of all synonyms
    :rtype: {JsonResponse}
    """
    querylist = list(Synonym.objects.filter(Q(synonym_status__in=['Beslutad', 'Tillåten', 'Avråds', 'Rekommenderad'])).values())
    
    for index, synonym_qs in enumerate(querylist):    
        try:
            term = Begrepp.objects.get(Q(pk=synonym_qs.get('begrepp_id')) & Q(status__in=['Avråds','Avställd','Beslutad'])).term
            querylist[index]['term'] = term
        except ObjectDoesNotExist as e:
            pass
    return JsonResponse(querylist, json_dumps_params={'ensure_ascii':False}, safe=False)
