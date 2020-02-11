from django.shortcuts import render
from django.http import HttpResponse
from .models import Begrepp

def index(request):
    return render(request, 'index.html')

def view2(request):
    return render(request,'view2.html')

def view3(request):
    return render(request, 'view3.html')

def autocompleteModel(request):
    if request.is_ajax():
        q = request.GET.get('term', '').capitalize()
        search_qs = Begrepp.objects.filter(name__startswith=q)
        results = []
        print(q)
        for r in search_qs:
            results.append(r.FIELD)
        data = json.dumps(results)
    else:
        data = 'fail'
    mimetype = 'application/json'
    return HttpResponse(data, mimetype)