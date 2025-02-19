from django.contrib import admin, messages
from django.db.models import Q, Count
from django.utils.safestring import mark_safe
from django.contrib.auth.models import Group
from term_list.models import (Dictionary, Concept, Attribute)
from django.core.exceptions import ObjectDoesNotExist

from term_list.forms import (ExcelImportForm,
                          ColumnMappingForm)
from django.core.exceptions import ValidationError

from django.urls import path, reverse
from django.shortcuts import render, redirect
from django.utils.html import format_html

import pandas as pd
import io
import base64
import json
import difflib
import html

import logging
logger = logging.getLogger(__name__)

from django.http import JsonResponse


from pdb import set_trace

def add_non_breaking_space_to_status(status_item):

    if status_item:
        length = len(status_item)
        length_to_add = 12 - length
        for x in range(length_to_add):
            if x % 2 == 0:
                status_item += '&nbsp;'
            else:
                status_item = '&nbsp;' + status_item
        return mark_safe(status_item)

def conditional_lowercase(cell):
    words = cell.split(' ')
    new_word = []
    for word in words:
        if word.isupper():
            new_word.append(word.strip())
        else:
            new_word.append(word.strip().lower())
    return ' '.join(new_word)

class DictionaryRestrictAdminMixin:
    """
    A mixin that restricts access to objects based on the user's group
    memberships and their relation to dictionaries.
    """

    def get_accessible_dictionaries(self, request):
        """
        Returns the dictionaries accessible to the user's groups.
        """
        if request.user.is_superuser:
            return Dictionary.objects.all()  # Superusers can access all dictionaries

        user_groups = request.user.groups.all()

        # Filter dictionaries that are accessible to the user's groups
        accessible_dictionaries = Dictionary.objects.filter(
            groups__in=user_groups
        ).distinct()

        return accessible_dictionaries

class DictionaryRestrictedOtherModelAdminMixin:
    """
    A mixin that restricts access to objects based on the user's group
    memberships and their relation to dictionaries.
    """

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs

        user_groups = request.user.groups.all()

        # Filter dictionaries that are accessible to the user's groups
        accessible_dictionaries = Dictionary.objects.filter(
            groups__in=user_groups
        ).distinct()

        # Filter the queryset based on the accessible dictionaries
        return qs.filter(begrepp__dictionaries__in=accessible_dictionaries)

class ConceptFileImportMixin:

    def __init__(self, *args, **kwargs):
        logger.info("ConceptFileImportMixin initialized")  # Debug message
        super().__init__(*args, **kwargs)

    def get_urls(self):

        logger.info('Prepending ConceptFileImportMixin urls to admin urls')
        custom_urls = [
            path('importera-excel/', 
                 self.admin_site.admin_view(self.import_excel_view), 
                 name="import_excel_view"),
        ]
        urls = super().get_urls()

        return custom_urls + urls

    # This will add the button to the changelist view
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['import_excel_url'] = reverse('admin:import_excel_view')  # Dynamically add the URL to the context
        return super().changelist_view(request, extra_context=extra_context)
    
    def get_draft_mappings(self, excel_columns, model_fields):

        """
        Function to get draft mappings by matching Excel columns to model fields.
        """
        draft_mapping = {}
        for column in excel_columns:
            # Use difflib to find the closest match for each column in the model fields
            closest_match = difflib.get_close_matches(column, model_fields, n=1)
            if closest_match:
                draft_mapping[column] = closest_match[0]  # Take the best match
            else:
                draft_mapping[column] = None  # No close match found
        return draft_mapping
    
    def import_excel_view(self, request):

        if 'apply' in request.POST:
            # Process the uploaded file and prepare it for column mapping
            form = ExcelImportForm(request.POST, request.FILES)
            if form.is_valid():
                excel_file = request.FILES['excel_file']
                file_data = excel_file.read()
                encoded_excel_file = base64.b64encode(file_data).decode('utf-8')

                # Read the Excel file
                df = pd.read_excel(io.BytesIO(file_data), engine='openpyxl')

                columns = df.columns.tolist()
                model_fields = [f.name for f in Concept._meta.get_fields()]

                # Get available dictionaries based on user group membership
                available_dictionaries = self.get_accessible_dictionaries(request)

                # Check if the dictionary column is present in the Excel file
                dictionary_in_excel = 'dictionary' in df.columns

                # Get draft mappings
                draft_mapping = self.get_draft_mappings(columns, model_fields)

                
                # Show the mapping form
                initial_mapping = {col: draft_mapping[col] for col in columns}

                initial_data = {
                    'excel_file': encoded_excel_file
                }

                # Merge with the initial_mapping
                initial_data.update(initial_mapping)

                mapping_form = ColumnMappingForm(
                    columns=columns,
                    model_fields=model_fields,
                    available_dictionaries=[(dict.dictionary_id, 
                                             dict.dictionary_name) for dict in available_dictionaries],
                    initial=initial_data,
                )

                return render(request, 'admin/column_mapping.html', {
                    'mapping_form': mapping_form,
                    'dictionary_in_excel': dictionary_in_excel  # Pass whether dictionary is in the Excel file
                })

        # Step 2: Handle intermediate confirmation page
        if 'apply_mapping' in request.POST:
            # Assume form contains the parsed data from the uploaded file

            column_mapping = json.loads(request.POST.get('column_mapping_json'))
            df = pd.read_excel(io.BytesIO(base64.b64decode(request.POST.get('excel_file'))), engine='openpyxl')
            column_headers = df.columns.to_list()
            available_dictionaries = self.get_accessible_dictionaries(request)
    
            updated_records = []
            concept_data_list = []
            
            for _, row in df.iterrows():
                data = {column_mapping[col]: row[col] for col in df.columns if column_mapping.get(col)}
                data['term'] = conditional_lowercase(data.get('term'))
                data['definition'] = data.get('definition').replace('\u200b','').strip()            
                data['dictionary'] = column_mapping.get('dictionary') 
                
                try:        
                    
                    existing_begrepp = Concept.objects.get(term=data.get('term'), dictionaries__in=available_dictionaries)
                                            
                    is_changed = False
                    for field, value in data.items():
                        # Get the corresponding field value from the existing object
                        existing_value = getattr(existing_begrepp, field, None)
                        if str(existing_value) != str(value):  # Convert both to string for safe comparison
                            is_changed = True
                            continue
                    
                    data['is_changed'] = is_changed        
                    data['is_new'] = True
                    concept_data_list.append(data)

                except Concept.DoesNotExist:
                    # Create a new Concept if it doesn't exist
                    data['is_changed'] = False 
                    data['is_new'] = True   
                    concept_data_list.append(data)
            
            #Render the confirmation page
            return render(request, 'admin/confirm_mapping.html', {
                'begrepp_data_list': concept_data_list,
                'begrepp_data_list_json': json.dumps(concept_data_list, ensure_ascii=False),
                'column_headers': column_headers,
            })

        # Step 3: Final creation or update after confirmation
        if 'confirm_import' in request.POST:

            unescaped_data = html.unescape(request.POST.get('begrepp_data_list'))

            try:
                concept_data_list = json.loads(unescaped_data)
            except json.JSONDecodeError as e:
                messages.error(request, f"Error decoding JSON: {e}")
                return redirect("admin:term_list_begrepp_changelist")

            for data in concept_data_list:
                # Remove 'dictionaries' from the data dictionary since we can't pass M2M fields to update_or_create, 
                # additionally is_update is not part of the Concept model.
                
                dictionary_id = data.pop('dictionary', [])
                data.pop('is_changed', None)
                data.pop('is_new', None)

                begrepp_instance, created = Concept.objects.update_or_create(term=data.get('term'), defaults=data)
                
                # Handle the M2M relation (dictionaries)
                if dictionary_id:
                    dictionaries_to_add = Dictionary.objects.filter(dictionary_id__in=[dictionary_id])
                    begrepp_instance.dictionaries.set(dictionaries_to_add)

            messages.success(request, "Data från filen importerad!")
            return redirect("admin:term_list_begrepp_changelist")

        # If no valid form submission, render the upload page again
        form = ExcelImportForm()
        return render(request, 'admin/excel_upload.html', {
            'form': form
        })

#@csrf_exempt
def fetch_attributes(request):
    dictionary_id = request.GET.get('dictionary_id')
    if not dictionary_id:
        return JsonResponse({'error': 'No dictionary ID provided'}, status=400)
    try:
        if not Dictionary.objects.get(pk=dictionary_id):
            pass
    except ObjectDoesNotExist:
        return JsonResponse({'error': 'Dictionary with that ID not found'}, status=404)

    
    # Fetch attributes linked to the dictionary's groups
    attributes = Attribute.objects.filter(groups__dictionaries__dictionary_id=dictionary_id).distinct()

    # Serialize attributes
    attribute_data = [
        {'id': attr.id, 'display_name': attr.display_name, 'data_type': attr.data_type}
        for attr in attributes
    ]
    return JsonResponse({'attributes': attribute_data})

class DuplicateTermFilter(admin.SimpleListFilter):
    title = 'Term dubbletter'
    parameter_name = 'duplicates'

    def lookups(self, request, model_admin):
        # Define the filter options: 'Show duplicates' or 'Show all'
        return (
            ('duplicates', 'Visa dupliceringar'),
        )

    def queryset(self, request, queryset):
        # If 'duplicates' is selected, filter for terms that have duplicates
        if self.value() == 'duplicates':
            # Get terms that have more than one entry (i.e., duplicates)
            duplicate_terms = queryset.values('term').annotate(term_count=Count('term')).filter(term_count__gt=1)
            # Filter queryset to include only those terms
            return queryset.filter(term__in=[item['term'] for item in duplicate_terms]).order_by('term')
        return queryset


class DictionaryFilter(admin.SimpleListFilter):
    title = 'term_list'
    parameter_name = 'term_list'

    def lookups(self, request, model_admin):
        # Returns a list of tuples. The first element in each tuple is the coded value for the option that will appear in the URL query. The second element is the human-readable name for the option that will appear in the right sidebar.
        dictionaries = Dictionary.objects.values('dictionary_name').annotate(name_count=Count('dictionary_name')).filter(name_count__gt=0).distinct()
        lookups = [(dictionary['dictionary_name'], dictionary['dictionary_name']) for dictionary in dictionaries]
        lookups.append(('no_dictionary', 'Inga Ordböcker'))
        return  lookups

    def queryset(self, request, queryset):
        if self.value() == 'no_dictionary':
            # Filter for Concept instances without an associated Dictionary
            return queryset.filter(dictionaries__isnull=True)
        elif self.value():
            # Filter for Concept instances with the selected Dictionary name
            return queryset.filter(dictionaries__dictionary_name=self.value())
        return queryset
