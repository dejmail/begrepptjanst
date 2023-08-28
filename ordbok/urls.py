
from django.urls import include, path
from ordbok import views
from ordbok import admin as admin_views


urlpatterns = [
    path("", views.begrepp_view, name="begrepp"),
    path('kommentera/', views.kommentera_term, name="kommentera_term"),
    path('begrepp-forklaring/', views.begrepp_förklaring_view, name="begrepp_förklaring"),
    path('requesttermform/', views.hantera_request_term, name='hantera_term_request'),
    path('unread-comments/', views.return_number_of_comments, name='unread_comments'),
    path('prenumera/', views.prenumera_till_epost, name="email_subscribe"),
    path('no-search-result/', views.no_search_result, name='no_search_result'),
    path('autocomplete-suggestions/<str:attribute>/<search_term>/', views.autocomplete_suggestions, name='autocomplete_suggestions'),
    
    path('json/begrepp/', views.all_accepted_terms, name='all_accepted_terms'),
    path('json/begrepp/<int:id>', views.get_term, name='get_terms'),
    path('json/begrepp/all/', views.all_non_beslutade_begrepp, name='all_non_beslutade_begrepp'),
    path('json/synonymer/', views.all_synonyms, name='all_synonyms'),
    
    path('export/attrs/', admin_views.BegreppAdmin.export_chosen_attrs_view, name='export_chosen_attrs'),
]
