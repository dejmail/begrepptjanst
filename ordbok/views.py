import json
from pdb import set_trace

from django.forms.models import model_to_dict
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from datetime import datetime
from django.db import connection, transaction
from django.core.mail import EmailMessage
from ordbok.models import Begrepp, Bestallare, Doman, Synonym
from .forms import TermRequestForm, OpponeraTermForm, BekräftaTermForm

def autocompleteModel(request):
    if request.is_ajax():
        q = request.GET.get('txtSearch', '')
        search_qs = Begrepp.objects.filter(term__icontains=q)
        print('length of search result', len(search_qs))
        results = []
        for r in search_qs:
            #print(r)
            results.append(r.term)
        data = json.dumps(results)
    else:
        data = 'fail'
    mimetype = 'application/json'
    return HttpResponse(data, mimetype)

def retur_komplett_förklaring_custom_sql(url_parameter):
    
    cursor = connection.cursor()
    sql_statement = f"SELECT\
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
                                ordbok_begrepp.id = {int(url_parameter)};"
    
    result = cursor.execute(sql_statement)
    
    column_names = [i[0] for i in result.description]
    retur_records = result.fetchall()
    
    return dict(zip(column_names, retur_records[0]))

def begrepp_view(request):
    ctx = {}
    url_parameter = request.GET.get("q")
    if url_parameter:
 
        begrepp = Begrepp.objects.filter(term__icontains=url_parameter)
    else:
    #    begrepp = False
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
        set_trace()
        exact_term = retur_komplett_förklaring_custom_sql(url_parameter)
    else:
        term_json = 'Error - Record not found'

    
    if request.is_ajax():
        #set_trace()
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

    if request.method == 'POST':
        form = OpponeraTermForm(request.POST)
        if form.is_valid():
            pass
        return HttpResponse('Tack! Dina synpunkter har skickats in för granskning')

    else:
        form = OpponeraTermForm()
    
    return render(request, 'opponera_term.html', {'opponera': form})

def bekräfta_term(request):

    url_parameter = request.GET.get("q")

    if request.method == 'GET':
        inkommande_term = Begrepp(term=url_parameter)
        form = BekräftaTermForm(initial={'term_id' : inkommande_term})

    if request.method == 'POST':
    
        form = BekräftaTermForm(request.POST)
        if form.is_valid():
            kopplad_domän = Doman()
            kopplad_domän.begrepp = Begrepp.objects.get(term=form.cleaned_data.get('term_id'))
            kopplad_domän.domän_namn = form.cleaned_data.get('workstream')
            kopplad_domän.domän_kontext = form.cleaned_data.get('kontext')
            
            #SomeModel.objects.filter(id=id).delete()
            kopplad_domän.save()

            return HttpResponse('Tack! Begrepp definitionen bekräftades')        
    
    else:
        return render(request, 'bekrafta_term.html', {'bekräfta': form})