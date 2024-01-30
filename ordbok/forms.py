from django import forms
from .models import Begrepp, BegreppExternalFiles
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column
from crispy_forms.layout import Field
from django.core.exceptions import ValidationError
from pdb import set_trace

from .models import STATUS_VAL

class CustomDateInput(forms.DateInput):
    input_type = 'date'

class TermRequestForm(forms.Form):

    def clean(self):
        cleaned_data = super().clean()
        
        return cleaned_data

    def clean_name(self):
        namn =  self.cleaned_data.get('namn')
        return namn

    def clean_epost(self):
        epost = self.cleaned_data.get('epost')
        return epost
    
    def clean_telefon(self):
        telefon = self.cleaned_data.get('telefon')
        return telefon
    
    def clean_kontext(self):
        kontext = self.cleaned_data.get('kontext')
        return kontext

    def clean_begrepp(self):
        begrepp = self.cleaned_data.get('begrepp')
        return begrepp

    begrepp = forms.CharField(max_length=254, label="Skriv in den term som används för att beksriva begreppet", widget = forms.TextInput)
    kontext = forms.CharField(widget=forms.Textarea, label="Hur används termen? I vilket sammanghang?")
    namn = forms.CharField(max_length=100)
    epost =  forms.EmailField(max_length=254, label="E-post")
    telefon = forms.CharField(max_length=30, label="Kontakt",  widget=forms.TextInput(attrs={'placeholder': "telefonnummer"})) 
    file_field = forms.FileField(widget=forms.ClearableFileInput(), label="Bifogar en skärmklipp eller komprimerad fil som kan hjälp oss", required=False)

class KommenteraTermForm(forms.Form):

    namn = forms.CharField()
    epost = forms.EmailField()
    telefon = forms.CharField(max_length=30, label="Kontakt", widget=forms.TextInput(attrs={'placeholder': "telefonnummer"}))
    resonemang = forms.CharField(widget=forms.Textarea, max_length=2000, label='Kommentar')
    term = forms.CharField(widget=forms.HiddenInput())
    file_field = forms.FileField(widget=forms.ClearableFileInput(), label="Bifogar en skärmklipp eller komprimerad fil som kan hjälp oss", required=False)

class ExternalFilesForm(forms.ModelForm):

    class Meta:
        model = BegreppExternalFiles
        exclude = ()

    begrepp = forms.CharField(widget=forms.HiddenInput())  
    kommentar = forms.CharField(widget=forms.HiddenInput())  
    support_file = forms.FileField()


class BegreppForm(forms.ModelForm):
    
    class Meta:
        model = Begrepp
        exclude = ()
        help_texts = {'term': 'Rullistan visar termer redan i DB',
                      'definition': 'Visas som HTML på framsidan',
                      'källa': 'Rullistan visar termer redan i DB'}

    def __init__(self, *args, config_option=None, **kwargs):
        super().__init__(*args, **kwargs)
        if config_option == False:  # Adjust this condition based on your requirement
            # Remove the 'dictionaries' field from the form
            self.fields.pop('dictionaries')
    
    
    def clean(self):
        
        cleaned_definition = self.cleaned_data.get('definition')
        
        if any((c in ['{', '}', '½']) for c in cleaned_definition):
            raise forms.ValidationError({'definition' : 'Får inte ha { } eller ½ i texten'})
        
        return self.cleaned_data
    
    

class BegreppExternalFilesForm(forms.ModelForm):

    support_file = forms.FileField(label='Bifogad fil')
    
    class Meta:
        model = BegreppExternalFiles
        exclude = ()
        help_texts = {'kommentar' : 'Kan länkas till en kommentar också, men behövs inte'}

class ChooseExportAttributes(forms.Form):

    attribut = forms.MultipleChoiceField(required=False)
    term = forms.CharField(widget=forms.HiddenInput(), required=False)