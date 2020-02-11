
from django.urls import include, path
from . import views
from .views import autocompleteModel
from ordbok import views as ordbok_views

urlpatterns = [
    path('', views.index, name='index'),
    path('view2', views.view2, name= "view2"),
    path('view3', views.view3 , name="view3"),
    path('base', views.base, name="base"),
    path("begrepp/", ordbok_views.begrepp_view, name="begrepp"),

]

