
from django.urls import include, path
from ordbok import views
from ordbok import admin as admin_views


urlpatterns = [
    path("", views.concept_view, name="concept"),
    path('kommentera/<int:term_id>', views.submit_comments_for_a_term, name="comment_form"),
    path('begrepp-forklaring/', views.get_single_term_view, name="begrepp_förklaring"),
    path('request-new-term/', views.request_new_term, name='request_new_term'),
    path('unread-comments/', views.return_number_of_comments, name='unread_comments'),
    path('prenumera/', views.subscribe_to_newsletter, name="email_subscribe"),
    path('hjalp/', views.help_text_view, name="help_text"),
    path('no-search-result/', views.no_search_result, name='no_search_result'),
    path('autocomplete-suggestions/<str:attribute>/<search_term>/', views.autocomplete_suggestions, name='autocomplete_suggestions'),
    
    path('json/begrepp/', views.all_accepted_terms, name='all_accepted_terms'),
    path('json/begrepp/<int:id>', views.get_term, name='get_terms'),
    path('json/begrepp/all/', views.all_non_beslutade_begrepp, name='all_non_beslutade_begrepp'),
    path('json/synonymer/', views.all_synonyms, name='all_synonyms'),
    
    path('export/attrs/', admin_views.BegreppAdmin.export_chosen_attrs_view, name='export_chosen_attrs'),
]
