from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from ordbok.models import Begrepp
from django.template.loader import render_to_string
from django.core import serializers
import json
from django.http import JsonResponse
from pdb import set_trace
from django.forms.models import model_to_dict
from django.core.serializers.json import DjangoJSONEncoder



def index(request):
    return render(request, 'index.html')

def view2(request):
    return render(request,'view2.html')

def view3(request):
    return render(request, 'view3.html')

def base(request):
    return render(request, 'base.html')

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

def begrepp_view(request):
    ctx = {}
    url_parameter = request.GET.get("q")

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
        exact_term = Begrepp.objects.get(id__exact=url_parameter)
        model_dict = model_to_dict(exact_term)
    else:
        term_json = 'Error - Record not found'

    ctx["begrepp"] = exact_term
    if request.is_ajax():
        html = render_to_string(template_name="term_forklaring.html", context={"begrepp": model_dict})
        data_dict = {"html_from_view": html}
        
        return HttpResponse(json.dumps(data_dict), content_type="application/json")

    return render(request, "base.html", context=ctx)