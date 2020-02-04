from django.shortcuts import render
from django.http import HttpResponse


def index(request):
    return render(request, 'index.html')

def view2(request):
    return render(request,'view2.html')

def view3(request):
    return render(request, 'view3.html')

