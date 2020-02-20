
from django.urls import include, path
from . import views
from .views import autocompleteModel
from ordbok import views as ordbok_views

urlpatterns = [
    path("", ordbok_views.begrepp_view, name="begrepp"),
    path("term_opponering/", ordbok_views.opponera_term, name="opponera_term"),
    path("term_bekraftelse/", ordbok_views.bekräfta_term, name="bekräfta_term"),
    path("begrepp_forklaring/", ordbok_views.begrepp_förklaring_view, name="begrepp_förklaring"),
    path('requesttermform/', ordbok_views.hantera_request_term, name='hantera_term_request')

]

