from django import forms
from .models import (
    Dictionary, 
    Concept, 
    ConceptExternalFiles, 
    AttributeValue,
    ConfigurationOptions
)

from django import forms
from django.core.exceptions import ValidationError
from pdb import set_trace

import logging
import json
from .models import ConfigurationOptions

logger = logging.getLogger(__name__)

class CustomDateInput(forms.DateInput):
    input_type = 'date'

class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

    def __init__(self, attrs=None):
        default_attrs = {
            "multiple": True,
            "aria-label": "Ladda upp filer som kan hjälpa oss",
            "aria-describedby": "file-upload-help",
        }
        if attrs:
            default_attrs.update(attrs)
        super().__init__(default_attrs)


class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result

class GroupFilteredModelForm(forms.ModelForm):
    """ A form that filters choices based on the logged-in user's group membership. """

    def __init__(self, *args, **kwargs):
        # Pass the request user to the form
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.user and not self.user.is_superuser:
            # Filter queryset for fields that need group-based filtering
            self.filter_queryset()

    def filter_queryset(self):
        user = self.user
        if user and not user.is_superuser:
            user_groups = user.groups.all()
            domain_ids = Dictionary.objects.filter(groups__in=user_groups).values_list('dictionary_id', flat=True)
            begrepp_ids = Concept.objects.filter(begrepp_fk__dictionary_id__in=domain_ids).values_list('id', flat=True)
            self.fields['begrepp'].queryset = Concept.objects.filter(id__in=begrepp_ids)

class TermRequestForm(forms.Form):

    def __init__(self, *args, **kwargs):
        super(TermRequestForm, self).__init__(*args, **kwargs)
        self.fields['dictionary'].widget.attrs['readonly'] = True


    def clean(self):
        cleaned_data = super().clean()        
        return cleaned_data

    def clean_name(self):
        namn =  self.cleaned_data.get('namn')
        return namn

    def clean_email(self):
        epost = self.cleaned_data.get('epost')
        return epost
    
    def clean_dictionary(self):
        
        dictionary = Dictionary.objects.filter(dictionary_long_name=self.cleaned_data.get('dictionary')).first()
                # Assuming you're checking if the dictionary exists in the database
        if not dictionary:
            raise ValidationError("The dictionary does not exist.")

        return dictionary

    def clean_context(self):
        kontext = self.cleaned_data.get('kontext')
        return kontext

    def clean_concept(self):
        begrepp = self.cleaned_data.get('begrepp')
        return begrepp

    begrepp = forms.CharField(max_length=254, label="Term som representerar begreppet", widget = forms.TextInput)
    dictionary = forms.CharField(max_length=64, label="Ordlista")
    kontext = forms.CharField(widget=forms.Textarea, label="Beskriv hur begreppet används:") 
    namn = forms.CharField(max_length=100)
    epost =  forms.EmailField(max_length=254, label="E-post")
    file_field = MultipleFileField(label="Bifogar en/flera skärmklipp eller filer som kan hjälp oss", required=False)
      
class PrettyDecodedJSONWidget(forms.Textarea):
    def format_value(self, value):
        try:
            # Handle stringified JSON
            if isinstance(value, str):
                value = json.loads(value)
            return json.dumps(value, indent=2, ensure_ascii=False)
        except Exception:
            return value
        
class ConfigurationOptionsForm(forms.ModelForm):
    class Meta:
        model = ConfigurationOptions
        fields = '__all__'
        widgets = {
            'config': PrettyDecodedJSONWidget(attrs={'cols': 80, 'rows': 20}),
        }

class CommentTermForm(forms.Form):

    name = forms.CharField(
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "aria-label": "Ange ditt namn"  # ARIA label added
        }),
        label="Namn",  # Ensures proper label in crispy forms
        max_length=255
    )
    epost = forms.EmailField(label="E-postadress", widget=forms.EmailInput(attrs={
            "class": "form-control",
            "id": "prenumera",
            "placeholder": "E-postadress",
            "aria-label": "E-postadress"
        }),
        required=True
        )
    comment = forms.CharField(
        widget=forms.Textarea(attrs={
            "class": "form-control",
            "aria-label": "Skriv din kommentar här",  # ARIA label added
        }),
        max_length=2000,
        label="Kommentar"
    )
    
    term = forms.CharField(
        widget=forms.HiddenInput(attrs={
            "aria-hidden": "true"  # Hidden input does not need a visible label
        })
    )

    file_field = MultipleFileField(
        label="Bifogar en/flera skärmklipp eller filer som kan hjälpa oss",
        required=False
    )

class ExternalFilesForm(forms.ModelForm):

    class Meta:
        model = ConceptExternalFiles
        exclude = ()

    begrepp = forms.CharField(widget=forms.HiddenInput())  
    kommentar = forms.CharField(widget=forms.HiddenInput())  
    support_file = forms.FileField()

class ExcelImportForm(forms.Form):
    excel_file = forms.FileField(label='Excel fil')

class ColumnMappingForm(forms.Form):

    excel_file = forms.CharField(widget=forms.HiddenInput())
    dictionary = forms.ChoiceField(label="Select Dictionary", required=False)  # Add dictionary field here

    def __init__(self, *args, **kwargs):
        columns = kwargs.pop('columns')
        model_fields = kwargs.pop('model_fields')
        available_dictionaries = kwargs.pop('available_dictionaries', [])  # Pass available dictionaries
        super().__init__(*args, **kwargs)
        
        # Dynamically create form fields for mapping columns to model fields
        
        for col in columns:
            self.fields[col] = forms.ChoiceField(
                choices=[(None, '---')] + [(field, field) for field in model_fields],
                required=False,
                label=f"Mappa excel kolumn '{col}' mot model attribut"
            )
        
        # If dictionaries are available, allow the user to choose one
        if available_dictionaries:
            self.fields['dictionary'].choices = [(None, '---')] + [(dict_id, dict_name) for dict_id, dict_name in available_dictionaries]

from django import forms
from .models import AttributeValue
from django.forms.widgets import HiddenInput


class AttributeValueInlineForm(forms.ModelForm):
    class Meta:
        model = AttributeValue
        fields = ['value_string', 'value_text', 'value_integer', 'value_decimal', 'value_boolean', 'value_url']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.attribute_id:
            attribute = self.instance.attribute
            data_type = attribute.data_type
            display_name = attribute.display_name  # ✅ Get the attribute's display name

            # ✅ Map attribute data type to the correct field name
            field_map = {
                'string': 'value_string',
                'text': 'value_text',
                'integer': 'value_integer',
                'decimal': 'value_decimal',
                'boolean': 'value_boolean',
                'url': 'value_url'
            }

            for field_name, field in self.fields.items():
                if field_name != field_map.get(data_type, ''):
                    self.fields[field_name].widget = HiddenInput()  # ✅ Hide irrelevant fields
                else:
                    self.fields[field_name].label = ''

class ConceptForm(GroupFilteredModelForm):
    
    class Meta:
        model = Concept
        exclude = ()
        fields = '__all__'
        help_texts = {'term': 'Rullistan visar termer redan i DB',
                      'definition': 'Visas som HTML på framsidan',
                      'källa': 'Rullistan visar termer redan i DB'}
        
    def __init__(self, *args, user=None, **kwargs):
        
        super().__init__(*args, **kwargs)
        self.user = user
        self.fields['status'] = forms.ChoiceField(
                choices=ConfigurationOptions.get_status_choices(),
                required=True
        )
        if user and not user.is_superuser and 'dictionaries' in self.fields:
            self.fields['dictionaries'].queryset = Dictionary.objects.filter(groups__in=user.groups.all()).distinct()

    def clean(self):
        
        cleaned_definition = self.cleaned_data.get('definition')
        cleaned_data = super().clean()

        
        if any((c in ['{', '}', '½']) for c in cleaned_definition):
            raise forms.ValidationError({'definition' : 'Får inte ha { } eller ½ i texten'})
        
        if (not hasattr(self, 'user')) or (self.user is None):
            raise Exception("Form is missing 'user'. Make sure it's passed from the admin.")

        user = self.user
        if user and not user.is_superuser:
            selected_dictionaries = cleaned_data.get("dictionaries")
            allowed = Dictionary.objects.filter(groups__in=user.groups.all()).distinct()

            unauthorized = selected_dictionaries.exclude(pk__in=allowed.values_list("pk", flat=True))
            if unauthorized.exists():
                raise ValidationError("Du har inte behörighet att koppla detta begrepp till en eller flera av de valda ordlistorna.")

        return cleaned_data
        
class ConceptExternalFilesForm(forms.ModelForm):

    support_file = forms.FileField(label='Bifogad fil')
    
    class Meta:
        model = ConceptExternalFiles
        exclude = ()
        help_texts = {'kommentar' : 'Kan länkas till en kommentar också, men behövs inte'}

class ChooseExportAttributes(forms.Form):

    attribut = forms.MultipleChoiceField(required=False)
    term = forms.CharField(widget=forms.HiddenInput(), required=False)