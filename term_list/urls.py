
from django.urls import include, path
from term_list import views, admin_functions
from term_list import admin as admin_views


urlpatterns = [
    path('', views.main_search_view, name="concept"),
    path('kommentera/', views.kommentera_term, name="kommentera_term"),
    path('begrepp-forklaring/', views.term_metadata_view, name="term_metadata"),
    path('requesttermform/', views.request_new_term, name='request_new_term'),
    path('unread-comments/', views.return_number_of_comments, name='unread_comments'),
    path('prenumera/', views.prenumera_till_epost, name="email_subscribe"),
    path('no-search-result/', views.no_search_result, name='no_search_result'),
    path('autocomplete-suggestions/<str:attribute>/<search_term>/', views.autocomplete_suggestions, name='autocomplete_suggestions'),
    path('get-dictionary-content/<str:dictionary>', views.get_dictionary_data, name="get_dictionary_details"),

    path('json/begrepp/', views.redirect_to_all_approved_terms, name='get_json_terms'),
    path('json/begrepp/<int:id>', views.get_term, name='get_terms'),
    path('json/begrepp/all/', views.all_accepted_terms, name='get_all_accepted_terms_as_json'),
    path('json/synonymer/', views.all_synonyms, name='all_synonyms'),

    
    path('export/attrs/', admin_views.BegreppAdmin.export_chosen_attrs_view, name='export_chosen_attrs'),
    path('fetch-attributes/', admin_functions.fetch_attributes, name='fetch_attributes'),

]
