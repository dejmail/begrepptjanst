from django import forms
from .models import Dictionary, Begrepp, BegreppExternalFiles
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column
from crispy_forms.layout import Field
from django.core.exceptions import ValidationError
from pdb import set_trace

from .models import STATUS_VAL

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
            begrepp_ids = Begrepp.objects.filter(begrepp_fk__dictionary_id__in=domain_ids).values_list('id', flat=True)
            self.fields['begrepp'].queryset = Begrepp.objects.filter(id__in=begrepp_ids)

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

    def clean_utländsk_term(self):
        utländsk_term = self.cleaned_data.get('utländsk_term')
        return utländsk_term

    def clean_begrepp(self):
        begrepp = self.cleaned_data.get('begrepp')
        return begrepp

    begrepp = forms.CharField(max_length=254, label="Term som representerar begreppet", widget = forms.TextInput)
    utländsk_term = forms.CharField(max_length=254, required=False, label="Engelsk term")
    kontext = forms.CharField(widget=forms.Textarea, label="Beskriv hur begreppet används:") 
    namn = forms.CharField(max_length=100)
    epost =  forms.EmailField(max_length=254, label="E-post")
    telefon = forms.CharField(max_length=30, label="Kontakt",  widget=forms.TextInput(attrs={'placeholder': "Telefon"})) 
    file_field = MultipleFileField(label="Bifogar en/flera skärmklipp eller filer som kan hjälp oss", required=False)

class KommenteraTermForm(forms.Form):

    namn = forms.CharField()
    epost = forms.EmailField()
    telefon = forms.CharField(max_length=30, label="Kontakt", widget=forms.TextInput(attrs={'placeholder': "Telefon"}))
    resonemang = forms.CharField(widget=forms.Textarea, max_length=2000, label='Kommentar')
    term = forms.CharField(widget=forms.HiddenInput())
    file_field = MultipleFileField(label="Bifogar en/flera skärmklipp eller filer som kan hjälp oss", required=False)

class ExternalFilesForm(forms.ModelForm):

    class Meta:
        model = BegreppExternalFiles
        exclude = ()

    begrepp = forms.CharField(widget=forms.HiddenInput())  
    kommentar = forms.CharField(widget=forms.HiddenInput())  
    support_file = forms.FileField()


class BegreppForm(GroupFilteredModelForm):
    
    class Meta:
        model = Begrepp
        exclude = ()
        help_texts = {'term': 'Rullistan visar termer redan i DB',
                      'definition': 'Visas som HTML på framsidan',
                      'källa': 'Rullistan visar termer redan i DB'}
        
    
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