
from django.urls import include, path
from . import views
from ordbok import views as ordbok_views
from ordbok import admin as admin_views


urlpatterns = [
    path("", ordbok_views.begrepp_view, name="begrepp"),
    path('term_kommentera/', ordbok_views.kommentera_term, name="kommentera_term"),
    path('begrepp_forklaring/', ordbok_views.begrepp_förklaring_view, name="begrepp_förklaring"),
    path('requesttermform/', ordbok_views.hantera_request_term, name='hantera_term_request'),
    path('unread_comments/', ordbok_views.return_number_of_comments, name='unread_comments'),
    path('prenumera/', ordbok_views.prenumera_till_epost, name="email_subscribe"),
    path('template-switcher/', ordbok_views.no_search_result, name='no_search_result'),
    path('autocomplete_suggestions/<str:attribute>/<search_term>/', ordbok_views.autocomplete_suggestions, name='autocomplete_suggestions'),
    path('export/attrs/', admin_views.BegreppAdmin.export_chosen_attrs_view, name='export_chosen_attrs'),

    path('json/begrepp/', views.all_beslutade_terms, name='all_beslutade_terms'),
    path('json/begrepp/<int:id>', views.get_term, name='get_terms'),
    path('json/begrepp/all/', views.all_non_beslutade_begrepp, name='all_non_beslutade_begrepp'),
    path('json/synonymer/', ordbok_views.all_synonyms, name='all_synonyms'),
    
]
