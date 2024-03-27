import logging
import re
from pdb import set_trace
from urllib.parse import unquote
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.utils.translation import gettext as _

from begrepptjanst.logs import setup_logging
from begrepptjanst.settings.production import EMAIL_HOST_PASSWORD
from ordbok.models import DEFAULT_STATUS
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.db import connection
from django.db.models import Q, When, Value, IntegerField, Case
from django.http import (
    HttpRequest, 
    HttpResponse, 
    HttpResponseRedirect, 
    JsonResponse
)
from django.db.models.query import QuerySet

from django.shortcuts import render
from django.template.loader import render_to_string
from django.urls import get_script_prefix
from django.utils.html import format_html


from ordbok.forms import KommenteraTermForm, TermRequestForm
from ordbok.functions import (HTML_TAGS, Xlator, mäta_förklaring_träff,
                              mäta_sök_träff, nbsp2space)
from ordbok.models import (
    Dictionary,
    TypeOfRelationship,
    Begrepp, 
    BegreppExternalFiles, 
    Bestallare,
    KommenteraBegrepp, 
    TermRelationship,
    ConfigurationOptions)

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

def get_search_results_from_db(search_parameter: str, dictionaries: list) -> QuerySet:

    """ Check whether the :model:`ordbok.Begrepp` contains entries related
    to the search terms. Order by certain parameters.

    Search terms are ordered by relevance
    Terms with status Publicera Ej, Ej Påbörjad are excluded
    
    Arguments: 
    url_parameter {str} -- Search string sent by the user
    :return: A queryset of matches
    :rtype: Queryset
        
    """

    child_terms = TermRelationship.objects.all().values_list('child_term_id')
    search_parameter_length = len(search_parameter)
    dictionary_length = len(dictionaries)
    if search_parameter_length > 2:
        queryset = Begrepp.objects.all().exclude(
                         status__in=['Publicera ej','Ej Påbörjad'],
                         id__in=child_terms
                     ).filter(
                     Q(id__contains=search_parameter) |
                     Q(term__icontains=search_parameter) |
                     Q(anmärkningar__icontains=search_parameter) |
                     Q(definition__icontains=search_parameter) |
                     Q(utländsk_term__icontains=search_parameter) |
                     Q(base_term__child_term__term__icontains=search_parameter)
                     ).distinct().prefetch_related()

        queryset = queryset.annotate(
            position=Case(
                When(Q(term__iexact=search_parameter), then=Value(1)),
                When(Q(term__istartswith=search_parameter), then=Value(2)),
                When(Q(term__icontains=search_parameter), then=Value(3)), 
                When(Q(utländsk_term__icontains=search_parameter), then=Value(5)),
                When(Q(definition__icontains=search_parameter), then=Value(6)), 
                default=Value(6), output_field=IntegerField()
            )
        )
    
    order_by = []
    if queryset.filter(position=1).exists():
        order_by.append('position')

    if order_by:
        queryset = queryset.order_by(*order_by)
    
    if (search_parameter_length > 2) and (
        dictionary_length > 0) and (dictionaries != ['']):
        queryset = queryset.filter(dictionaries__title__in=dictionaries)
    
    elif (search_parameter_length == 0) and (
        dictionary_length > 0):

        return Begrepp.objects.all().exclude(
                         status__in=[
                             'Publicera ej',
                             'Ej Påbörjad'
                             ],
                         id__in=child_terms
                     ).filter(
                         dictionaries__title__in=dictionaries
                         )
    
    elif (search_parameter_length == 0) and (dictionary_length == 0):

        return Begrepp.objects.all().exclude(
                         status__in=[
                             'Publicera ej',
                             'Ej Påbörjad'
                             ],
                     ).order_by('term')

    elif (search_parameter_length == 1 ) and (dictionary_length > 0):

        queryset = Begrepp.objects.all().exclude(
                    status__in=[
                        'Publicera ej',
                        'Ej Påbörjad'
                        ],
                    id__in=child_terms
                ).filter(
                    Q(dictionaries__title__in=dictionaries) &
                    Q(title__istartswith=search_parameter)
                    )

    return queryset

def filter_terms_by_first_letter(letter: str, dictionaries: list) -> QuerySet:

    """ A filter of :model:`ordbok.Begrepp` which returns a queryset 
    where the terms start with a certain letter.
    
    Arguments: 
    letter {str} -- String letter to filter with
    :return: A queryset of matches
    :rtype: Queryset
        
    """ 
    if len(dictionaries) > 0:
        queryset = Begrepp.objects.filter(
            ~Q(status="Publicera ej")
            ).filter(
                Q(term__istartswith=letter) &
                Q(dictionaries__title__in=dictionaries)
                ).distinct()
    else:
        queryset = Begrepp.objects.filter(
            ~Q(status="Publicera ej") &
            Q(term__istartswith=letter)
            )


    return queryset

def return_single_term(id: str) -> QuerySet:

    """Return a single match of :model:`ordbok.Begrepp`

    Arguments: 
    id {str} -- ID of the match requested by the user
    :return: A queryset match
    :rtype: Queryset

    >>>return_single_term(1) #doctest: +ELLIPSIS
    [<Begrepp: doctest_unpredicatable.Begrepp>]

    """

    return Begrepp.objects.get(pk=id)


def sort_results_according_to_search_term(queryset: QuerySet, search_term: str, position: int = 1) -> list:
    
    """Returns a sorted list based on "column" from list-of-dictionaries data.

    Arguments: 
    queryset {queryset} -- queryset containing terms to be returned to the UI
    url_parameter {str} -- The str with which to split each term with
    :return: Sorted list
    :rtype: list
    """
    if len(search_term) > 0:
        return sorted(queryset, key=lambda x: x.get('term').lower().split(search_term))
    else:
        return queryset


def highlight_search_term_i_definition(search_term: str, begrepp_dict_list: QuerySet) -> QuerySet:

    """Encapsulate the search string with HTML <mark> tag in the definition of 
    the term.

    Arguments: 
    search_term {str} -- the string which should be encased in HTML <mark>
    begrepp_dict_list -- class of type Queryset
    :return: A list of dictionaries
    :rtype: class of type Queryset
    """

    if len(search_term) > 0:
        for idx, begrepp in enumerate(begrepp_dict_list):
            begrepp_dict_list[idx]['definition'] = begrepp.get(
                'definition'
                ).replace(search_term, f'<mark>{search_term}</mark>')
    else:
        pass
        
    return begrepp_dict_list


def return_list_of_term_and_definition() -> QuerySet:
    
    
    """Return values "term" and "definition" from a queryset of all terms in
     :model:`ordbok.Begrepp`.

    Arguments: 
    :return: A queryset of dictionaries all terms excluding those with status 'Publicer ej'
    :rtype: class of type Queryset
    """

    result = Begrepp.objects.all().exclude(status='Publicera ej').values('term','definition')

    return result

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

    return clean_dict

def concatentate_all_dictionary_values_to_single_string(dictionary : dict, key : str):

    """ Concatenate all the dictionary values into a single string with a 
    spacer.

    Arguments: 
    dictionary {dict} -- 
    :return: A string created by joining all the values of a given key
    :rtype: str
    """
    
    # Run it through a filter function to take into account terms that have no definition
    # such as when they are a synonym or other 

    return ' ½ '.join(filter(None, map(str, [i.get(key) for i in dictionary])))

def creating_tooltip_hover_with_search_result(begrepp_dict_list: QuerySet, term_def_dict: dict, key: str = 'definition') -> QuerySet:

    """ Manipulate an incoming dictionary that has a 'term' and 'definition'
     key:value so that when a definition has references to other term/s
     within :model:`ordbok.Begrepp`, those references have a tooltip 
     connected show the definition on the UI.
     
     Arguments: 
    begrepp_dict_list {dict} -- A list of  key:values of the search results
    term_def_dict {} -- A list of all the term:definitions within :model:`ordbok.Begrepp`

    :return:
    :rtype:
    """
    
    # create dictionary of term:definition where the value contains the term definition and tooltip HTML
    term_def_dict_uncleaned = {
        record.get('term'):f'''<div class="definitiontooltip">{record.get('term').strip()}<div class="definitiontooltiptext">{record.get(key)}</div></div>&nbsp;''' for record in term_def_dict
        }

    term_def_dict = clean_dict_of_extra_characters(term_def_dict_uncleaned)

    # Would be good to be able to send a list of plurals that we could 
    # group togther in the pattern creation, but as Xlator is a dict
    # class, I'm not sure how to accomplish that.

    translator = Xlator(term_def_dict)
    
    # loop through each definition in the begrepp_dict_list and make one string with all the
    # definitions separated by the ' ½ ' string. Without the spaces, certain instances of words
    # are not detected at the boundaries. Send this string to the Xlator instantiation, and replace all 
    # the occurrences of begrepp in definitions with a hover tooltip text.
    
    joined_definitions = concatentate_all_dictionary_values_to_single_string(begrepp_dict_list, key)
    joined_definitions_minus_nbsp = nbsp2space(joined_definitions)
    gt_brackets, lt_brackets = find_all_angular_brackets(joined_definitions_minus_nbsp)
    
    joined_definitions_minus_nbsp = replace_non_html_brackets(joined_definitions_minus_nbsp, gt_brackets, lt_brackets)    
    
    # only here are the regex patterns created in Xlator, couple to the substitution 
    altered_strings = translator.xlat(joined_definitions_minus_nbsp)
    # resplit the now altered string back into a list
    resplit_altered_strings = altered_strings.split(' ½ ')
    
    for index, begrepp in enumerate(begrepp_dict_list):
        try:
           #if index == 292: set_trace()
           begrepp_dict_list[index][key] = resplit_altered_strings[index]
        except (re.error, KeyError) as e:
           #set_trace()
           logger.error(e)
    
    return begrepp_dict_list

def find_all_angular_brackets(bracket_string: str) -> tuple:

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

def replace_str_index(text: str, index: int, index_shifter: int, replacement: str) -> str:

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

def replace_non_html_brackets(edit_string: str, gt_brackets: list, lt_brackets: list) -> str:

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
    logger.debug(f'unedited string - {edit_string}')
    logger.debug(f'lt_brackets - {lt_brackets}')
    for lt_position in lt_brackets:
        edit_string = replace_str_index(edit_string, lt_position, index_shifter, '&lt;')
        logging.debug(f'edited_string - {edit_string}')
        index_shifter += 3
    
    logger.info(f'gt_brackets before index change - {gt_brackets}')
    
    stepped_range = [i*3-1 for i in range(1, 4)]
    logger.debug(f'stepped_range - {stepped_range}')
    zipped_lists = zip(stepped_range, gt_brackets)
    adjusted_gt_indexes = [x + y for (x, y) in zipped_lists]
    
    logger.debug(f'gt_brackets after index change - {adjusted_gt_indexes}')
    logger.debug('replacing > brackets')
    index_shifter=0
    for gt_position in adjusted_gt_indexes:        
        edit_string = replace_str_index(edit_string, gt_position, index_shifter, '&#62;')
        logging.debug(f'edited_string - {edit_string}')
        index_shifter += 4

    return edit_string

def mark_fields_as_safe_html(list_of_dict: list, fields: list) -> list:

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

def assemble_data_for_concept_view(search_parameter: str, 
                                   selected_dictionaries: list,
                                   page_number: int,
                                   display_all: bool) -> str:

    """Main method that couples together all the submethods needed to
    produce the HTML needed for the initial search view.

    Arguments:
    url_parameter {str} -- The search string sent by the user search
    :return: HTML page formatted with the search results
    :rtype: str
    """
    if (len(search_parameter) == 1) and (search_parameter.isupper()):
        search_request = filter_terms_by_first_letter(search_parameter, selected_dictionaries)
        highlight=False
    else: 
        search_request = get_search_results_from_db(search_parameter, 
                                                    selected_dictionaries) 

        logger.debug(f'len of search result = {len(search_request)}')
        highlight=True

    if not search_request:
        return None, None

    simple_terms = TermRelationship.objects.all().values_list('child_term', flat=True)
    search_request = search_request.exclude(id__in=simple_terms)

    # this is all the terms and definitions from the DB
    all_terms_and_definitions_dict = return_list_of_term_and_definition()
    return_list_dict = creating_tooltip_hover_with_search_result(
        begrepp_dict_list = search_request.values(),
        term_def_dict = all_terms_and_definitions_dict
        )

    if highlight==True:
        return_list_dict = highlight_search_term_i_definition(
            search_parameter, 
            return_list_dict
            )
    
    return_list_dict = sort_results_according_to_search_term(
        return_list_dict, 
        search_parameter
        )

    return_list_dict = mark_fields_as_safe_html(return_list_dict, ['definition',])

    if display_all==True:
        paginator = Paginator(return_list_dict, 10000)
    else:
        paginator = Paginator(return_list_dict, 10)
    
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        # if page is not an integer, deliver the first page
        page_obj = paginator.page(1)
    except EmptyPage:
        # if the page is out of range, deliver the last page
        page_obj = paginator.page(paginator.num_pages)
    
    related_terms  = TermRelationship.objects.filter(
        base_term__in=search_request.values_list('id', flat=True)
        )

    html = render_to_string(
        template_name="search-results.html", 
        context={
            'page_obj': page_obj,
            'färg_status' : färg_status_dict,
            'queryset' : search_request,
            'searched_for_term' : search_parameter,
            'dictionaries' : Dictionary.objects.all(),
            'selected_dictionaries' : selected_dictionaries,
            'relationship_types' : TypeOfRelationship.objects.all(),
            'related_terms' : related_terms,
            'config' : ConfigurationOptions.objects.all(),
            }
        )

    return html, return_list_dict

def is_request_ajax(request: HttpRequest) -> bool:

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return True
    else:
        return False

def concept_view(request: HttpRequest) -> HttpResponse:

    """ The view that processes the initial search from the user

    Arguments:
    request -- Incoming requrest object from the browser
    :return: HttpResponse object containing template and context
    :rtype: HttpResponse
    """
    search_term = request.GET.get("search_term")
    dictionaries = request.GET.getlist('dictionaries')
    display_all = bool(request.GET.get('display_all'))

    if (dictionaries == ['[]']) or (dictionaries == ['']):
        selected_dictionaries = []
    elif dictionaries:
        selected_dictionaries = dictionaries[0].split(',')
    else:
        selected_dictionaries = []

    if (request.GET.get('search_term') is not None):
        
        page_number = request.GET.get('page', 1)
        
        html, return_list_dict = assemble_data_for_concept_view(
            search_term, 
            selected_dictionaries, 
            page_number,
            display_all)
        
        if html is not None:
            mäta_sök_träff(sök_term=search_term,sök_data=return_list_dict, request=request)
            return HttpResponse(html)
        else:
            form = TermRequestForm(initial={'begrepp': search_term})
            return render(request, 
                          'request-term.html', 
                          context = {'form' : form,
                                     'dictionaries' : Dictionary.objects.all(),
                                     'selected_dictionaries' : selected_dictionaries,
                                     'searched_for_term' : search_term,
                                     'config' : ConfigurationOptions.objects.all(),
                                     }
                        )
    else:
        return render(request, "landing-page.html", context={
            'dictionaries' : Dictionary.objects.all(),
            'config' : ConfigurationOptions.objects.all(),
            }
        )

def get_single_term_view(request: HttpRequest) -> HttpResponse:

    """ View that processes the request for detailed information about a certain term

    Arguments:
    request: {HttpRequest} -- Request containing the id of the term of interest
    :return: HttpResponse object containing template and context of a single term
    :rtype: HttpResponse
    """

    url_parameter = request.GET.get("search_term")

    if url_parameter:
        single_term = return_single_term(url_parameter)
        
        related_terms = TermRelationship.objects.filter(base_term__id=single_term.id)
        
        mäta_förklaring_träff(sök_term=url_parameter, request=request)

        status_färg_dict = {'begrepp' : färg_status_dict.get(single_term.status),
                            'relationships' : related_terms}
        
        template_context = {'term': single_term,
                            'related_terms' : related_terms,
                            'dictionaries' : Dictionary.objects.all(),
                            'färg_status' : status_färg_dict}

    if request.method=='GET':
        if url_parameter is None:
            return render(request, "landing-page.html", context={})
        else:
            return render(request, "term-details.html", context=template_context)

    return render(request, "landing-page.html", context={})

def help_text_view(request: HttpRequest) -> HttpResponse:

    context = {'dictionaries' : Dictionary.objects.all()}

    return render(request, "help-text.html", context=context)

def request_new_term(request: HttpRequest) -> HttpResponse:

    """ Send the form data when a user wants to request a new term or 
    manage the POST data if the user submits the request.

    Arguments:
    request: {HttpRequest} -- Request object containing the POST information that
    will be saved to db for processing.
    :return: A HttpResponse containing a Bootstrap alert is sent back
    :rtype: {HttpResponse}
    """

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
            
            if Begrepp.objects.filter(term=request.POST.get('search_term')).exists():
                msg = _('Begreppet ni önskade finns redan i systemet, var god och sök igen.')
                return HttpResponse(f'''<div class="alert alert-danger text-center" id="ajax_response_message">
                            {msg}
                            </div>''')
            else:

                existing_beställare = Bestallare.objects.filter(
                    Q(beställare_namn__icontains=form.clean_name()) |
                    Q(beställare_email__icontains=form.clean_epost)
                                                    )

                if existing_beställare:
                    ny_beställare = existing_beställare.first()
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

                for filename in file_list:
                    new_file = BegreppExternalFiles()
                    new_file.begrepp = ny_term
                    new_file.support_file = filename
                    new_file.save()

                msg = _('Tack! Begrepp skickades in för granskning')
                return HttpResponse(f'''<div class="alert alert-success text-center" id="ajax_response_message">
                                {msg}
                                </div>''')
        else:
            
            return render(request, 'request-term.html', {'form': form,
                                                        'whichTemplate' : 'requestTerm',
                                                        'dictionaries' : Dictionary.objects.all()},
                                                        )

    elif request.method == 'GET':
       
        form = TermRequestForm(initial={'concept' : request.GET.get('search_term')})
        
        return render(request, 'request-term.html', {'form': form,
                                                    'dictionaries' : Dictionary.objects.all(),
                                                    'whichTemplate' : 'requestTerm',
                                                    'header' : 'Önskemål om nytt begrepp'})

    else:
        return render(request, 'landing-page.html', {})

def submit_comments_for_a_term(request: HttpRequest, term_id: int) -> HttpResponse:

    """ Send back either the form to allow the submission of comments or
    process the submitted form and save the data to db.

    Arguments:
    request {HttpRequest} -- HttpRequest object containing the POST/GET data
    :return: HttpResponse with a Bootstrap alert response if form submitted via 
    POST and saved successfully, or an empty form via GET that can be filled out.
    :rtype: {HttpResponse}
    """

    if request.method == 'GET':
        inkommande_term = Begrepp(pk=term_id)
        form = KommenteraTermForm(initial={'term' : inkommande_term})
        return render(request, 'comment-term.html', {'form': form,
                                                    'term' : inkommande_term,
                                                    'dictionaries' : Dictionary.objects.all()})

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

            msg = _('Tack för dina synpunkter.')

            return HttpResponse(f'''<div class="alert alert-success">\
                 {msg} </div>''')

def subscribe_to_newsletter(request: HttpRequest) -> HttpResponseRedirect:

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


def return_number_of_comments(request: HttpRequest) -> JsonResponse:
    
    """ Returns JSON with total number of comments, and total number of unread comments
    based on a status of Beslutad
    
    :return: JSON response containing the total number of comments, and total number of
    unread comments.
    :rtype: {JsonResponse}
    """
    

    if request.method == 'GET':
        total_comments = KommenteraBegrepp.objects.all()
        status_list = [i.get('status') for i in total_comments.values()]
        return JsonResponse({'unreadcomments' : len(status_list)-status_list.count("Beslutad"),
                             'totalcomments' : len(status_list)})

def no_search_result(request: HttpRequest) -> HttpResponse:

    """ A view that was used to provide different choices based on what the user
    chose to do if the initial search had zero results.

    :return: A HttpResponse with HTML template and context
    :rtype: {HttpResponse}
    """

    url_parameter = request.GET.get("q")
    if request.method == 'GET':        
         return render(request, "no_search_result.html", context={'searched_for_term' : url_parameter})    
 
def autocomplete_suggestions(request: HttpRequest, attribute: str, search_term: str) -> JsonResponse:

    """ In the admin pages, there are certain fields where it is helpful to have
    previously entered values shown to increase consistency across records.

    Arguments:
    request {HttpRequest}
    attribute {str} -- The attribute in the DB to apply the filter to. A field 
    in the form.
    search_term {str} -- String content that has been entered in the form
    :return: Json response containing a list of terms in the DB filtered by
    what has been typed in
    :rtype: {JsonResponse}
    """

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

def all_non_beslutade_begrepp(request: HttpRequest) -> JsonResponse:

    """ Returns a JSON response with all the terms that have status 'Beslutad'
    or 'Publicera ej'.

    :return: JSON response with a list of terms
    :rtype: {JsonResponse}
    """

    queryset = Begrepp.objects.all().filter(~Q(status='Beslutad') & 
                                            ~Q(status__icontains='publicera ej')).prefetch_related().values()


def merge_term_and_synonym(qs, syn_qs):

    for synonym in syn_qs:
        synonyms = {'tillåten': [],
                    'avråds' : []}
        try:
            if synonym.get('synonym_status').lower() == 'tillåten':
                synonyms['tillåten'].append(synonym.get('synonym'))
            else:
                synonyms['avråds'].append(synonym.get('synonym'))
            
            qs[synonym.get('begrepp_id')]['synonyms'] = synonyms
        except (IndexError, TypeError) as e:
            print(e)
    return qs

def all_accepted_terms(request: HttpRequest) -> JsonResponse:

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
    
    return JsonResponse(list(queryset), json_dumps_params={'ensure_ascii':False}, safe=False)

def get_term(request: HttpRequest, id: int) -> JsonResponse:

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
    qs_dict = {i.get('id'): i for i in queryset}

    merged_result = merge_term_and_synonym(qs_dict, synonym_qs)

    if queryset:
        return JsonResponse(merged_result, json_dumps_params={'ensure_ascii':False}, safe=False)
    else:
        return JsonResponse({'error' : 'No terms that match that id'})


def all_synonyms(request):

    """ Obtain all the synonyms from the :model:`ordbok.Synonym` and return
    a Queryset dictionary presented as JSON 

    :return: Json object of all synonyms
    :rtype: {JsonResponse}
    """
    querylist = list(Synonym.objects.all().values())

    for index, synonym_qs in enumerate(querylist):
        querylist[index]['term'] = Begrepp.objects.get(pk=synonym_qs.get('begrepp_id')).term

    return JsonResponse(querylist, json_dumps_params={'ensure_ascii':False}, safe=False)
