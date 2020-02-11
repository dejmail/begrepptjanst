from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from ordbok.models import Begrepp
from django.template.loader import render_to_string
import json
from django.http import JsonResponse

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