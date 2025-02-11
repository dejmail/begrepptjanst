from django import forms
from .models import (
    Dictionary, 
    Concept, 
    ConceptExternalFiles, 
    AttributeValue,
    Attribute)
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column
from crispy_forms.layout import Field
from django.core.exceptions import ValidationError
from pdb import set_trace

import logging
from .models import STATUS_CHOICES

logger = logging.getLogger(__name__)


class CustomDateInput(forms.DateInput):
    input_type = 'date'

class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

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

    def clean_non_swedish_term(self):
        non_swedish_terrm = self.cleaned_data.get('non_swedish_terrm')
        return non_swedish_terrm

    def clean_concept(self):
        begrepp = self.cleaned_data.get('begrepp')
        return begrepp

    begrepp = forms.CharField(max_length=254, label="Term som representerar begreppet", widget = forms.TextInput)
    dictionary = forms.CharField(max_length=64, label="Ordlista")
    non_swedish_terrm = forms.CharField(max_length=254, required=False, label="Engelsk term")
    kontext = forms.CharField(widget=forms.Textarea, label="Beskriv hur begreppet används:") 
    namn = forms.CharField(max_length=100)
    epost =  forms.EmailField(max_length=254, label="E-post")
    file_field = MultipleFileField(label="Bifogar en/flera skärmklipp eller filer som kan hjälp oss", required=False)


class KommenteraTermForm(forms.Form):

    namn = forms.CharField()
    epost = forms.EmailField()
    resonemang = forms.CharField(widget=forms.Textarea, max_length=2000, label='Kommentar')
    term = forms.CharField(widget=forms.HiddenInput())
    file_field = MultipleFileField(label="Bifogar en/flera skärmklipp eller filer som kan hjälp oss", required=False)

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


class AttributeValueInlineForm(forms.ModelForm):
    class Meta:
        model = AttributeValue
        fields = [] 

    def __init__(self, *args, **kwargs):
        
        self.concept = kwargs.pop('concept', None)
        super().__init__(*args, **kwargs)

        if not self.concept:
            logger.warning("Concept instance is missing. No attributes will be loaded.")
            return
        
        if self.concept:
            logger.debug(f"Filtering attributes for concept {self.concept}")
            group_ids = self.concept.dictionaries.values_list('groups', flat=True)
        
         # Get attributes related to the Concept's Dictionary and Group
        group_attributes = relevant_attributes = Attribute.objects.filter(groups__id__in=group_ids).distinct()
        logger.debug(f"Filtered attributes for concept {self.concept}: {group_attributes}")

        for name, field in self.fields.items():
            logger.debug(f"Field {name}: {field.widget}")
        # Skip processing for new instances
        if not self.instance or not self.instance.pk:
            return

        # Ensure the instance has a valid attribute
        if not self.instance.attribute:
            return

        logger.debug(f"Initialising form for AttributeValue: {self.instance}")

        for attribute in group_attributes:
            field_name = f"attribute_{attribute.id}"
            data_type = attribute.data_type            
            initial_value = self._get_initial_value(attribute)

        # Dynamically add the appropriate input field for the value
        # data_type = self.instance.attribute.data_type
        if data_type == 'string':
            self.fields['value'] = forms.CharField(
                initial=self.instance.value_string, required=False, label="Value"
            )
        elif data_type == 'text':
            self.fields['value'] = forms.CharField(
                widget=forms.Textarea, initial=self.instance.value_text, required=False, label="Value"
            )
        elif data_type == 'url':
            self.fields['value'] = forms.URLField(
                initial=self.instance.value_url, required=False, label="Value"
            )
        elif data_type == 'integer':
            self.fields['value'] = forms.IntegerField(
                initial=self.instance.value_integer, required=False, label="Value"
            )
        elif data_type == 'decimal':
            self.fields['value'] = forms.DecimalField(
                initial=self.instance.value_decimal, required=False, label="Value"
            )
        elif data_type == 'boolean':
            self.fields['value'] = forms.BooleanField(
                initial=self.instance.value_boolean, required=False, label="Value"
            )
        logger.debug(f"self.fields: {self.fields}")

    def _get_initial_value(self, attribute):

        """Fetch the initial value for an attribute."""
        try:
            attr_value = AttributeValue.objects.get(
                attribute=attribute, 
                term_id=self.concept.id
            )
            return attr_value.value_string  # Adjust based on the field type
        except AttributeValue.DoesNotExist:
            return None

    def clean(self):
        
        cleaned_data = super().clean()
        value = cleaned_data.get('value')

        # Ensure the value field corresponds to the attribute's data type
        if not self.instance.attribute:
            raise ValidationError("Attribute is missing.")
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        value = self.cleaned_data.get('value')

        # Map the value to the correct field in the model
        data_type = self.instance.attribute.data_type
        if data_type == 'string':
            instance.value_string = value
        elif data_type == 'text':
            instance.value_text = value
        elif data_type == 'url':
            instance.value_url = value
        elif data_type == 'integer':
            instance.value_integer = value
        elif data_type == 'decimal':
            instance.value_decimal = value
        elif data_type == 'boolean':
            instance.value_boolean = value

        if commit:
            instance.save()
        return instance
    
class ConceptForm(GroupFilteredModelForm):
    
    class Meta:
        model = Concept
        exclude = ()
        fields = '__all__'
        help_texts = {'term': 'Rullistan visar termer redan i DB',
                      'definition': 'Visas som HTML på framsidan',
                      'källa': 'Rullistan visar termer redan i DB'}
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def clean(self):
        
        cleaned_definition = self.cleaned_data.get('definition')
        
        if any((c in ['{', '}', '½']) for c in cleaned_definition):
            raise forms.ValidationError({'definition' : 'Får inte ha { } eller ½ i texten'})
        
        return self.cleaned_data

class ConceptExternalFilesForm(forms.ModelForm):

    support_file = forms.FileField(label='Bifogad fil')
    
    class Meta:
        model = ConceptExternalFiles
        exclude = ()
        help_texts = {'kommentar' : 'Kan länkas till en kommentar också, men behövs inte'}

class ChooseExportAttributes(forms.Form):

    attribut = forms.MultipleChoiceField(required=False)
    term = forms.CharField(widget=forms.HiddenInput(), required=False)