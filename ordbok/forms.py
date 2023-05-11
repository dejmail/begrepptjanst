from django import forms
from .models import Doman, Begrepp, BegreppExternalFiles
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column
from crispy_forms.layout import Field
from django.core.exceptions import ValidationError
from pdb import set_trace

from .models import STATUS_VAL

workstream_choices = [('Inte relevant','Inte relevant'),
('Akutsjukvård','Akutsjukvård'),
('DokumentationVårdproffesion','DokumentationVårdproffesion'),
('Resursstyrning','Resursstyrning'),
('Kärnfunktioner','Kärnfunktioner'),
('Läkemedel','Läkemedel'),
('Masterdata','Masterdata'),
('Materiallogistik','Materiallogistik'),
('MedicinskDokumentation','MedicinskDokumentation'),
('MödravårdObstetrik','MödravårdObstetrik'),
('Onkologi','Onkologi'),
('Operation','Operation'),
('Ordination&Beställningar','Ordination&Beställningar'),
('PAS','PAS'),
('Primärvård','Primärvård'),
('Psykiatri','Psykiatri'),
('Rapporter','Rapporter'),
('Övrigt/Annan','Övrigt/Annan')]


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



class TermRequestForm(forms.Form):

    def clean(self):
        cleaned_data = super().clean()
        workstream = cleaned_data.get("workstream")
        other = cleaned_data.get("other")
        
        if (workstream == 'Övrigt/Annan') and (other is None or other == ''):
        # Only do something if both fields are valid so far.
            self.add_error('other', 'Måste ge var begreppet används om du har valt Övrigt/Annan'
            )
            raise ValidationError("Måste ge var begreppet används om du har valt Övrigt/Annan")
        
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
    
    def clean_önskad_datum(self):
        return self.cleaned_data.get('önskad_datum')

    def clean_önskad_datum(self):
        return self.cleaned_data.get('önskad_datum')

    def clean_not_previously_mentioned_in_workstream(self):
        return self.cleaned_data.get('other')

    def clean_önskad_datum(self):
        önskad_datum = self.cleaned_data.get('önskad_datum')
        return önskad_datum

    def clean_kontext(self):
        kontext = self.cleaned_data.get('kontext')
        return kontext

    def clean_utländsk_term(self):
        utländsk_term = self.cleaned_data.get('utländsk_term')
        return utländsk_term

    def clean_begrepp(self):
        begrepp = self.cleaned_data.get('begrepp')
        return begrepp

    def clean_workstream(self):
        return self.cleaned_data.get('workstream')

    begrepp = forms.CharField(max_length=254, label="Term som representerar begreppet", widget = forms.TextInput)
    utländsk_term = forms.CharField(max_length=254, required=False, label="Engelsk term")
    kontext = forms.CharField(widget=forms.Textarea, label="Beskriv hur begreppet används:")
    workstream = forms.CharField(label='Var används begreppet', widget=forms.Select(choices=workstream_choices))
    other = forms.CharField(max_length=254, label="Om Övrigt/Annan, kan du specificera", required=False)
    önskad_datum = forms.DateField(widget=CustomDateInput, label="Önskad slutdatum för prioritering", help_text="Klicka på kalendar ikon på höger sidan")
    namn = forms.CharField(max_length=100)
    epost =  forms.EmailField(max_length=254, label="E-post")
    telefon = forms.CharField(max_length=30, label="Kontakt",  widget=forms.TextInput(attrs={'placeholder': "Skypenamn eller telefon"})) 
    file_field = MultipleFileField(label="Bifogar en/flera skärmklipp eller filer som kan hjälp oss", required=False)




class KommenteraTermForm(forms.Form):

    namn = forms.CharField()
    epost = forms.EmailField()
    telefon = forms.CharField(max_length=30, label="Kontakt", widget=forms.TextInput(attrs={'placeholder': "Skypenamn eller telefon"}))
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


class BegreppForm(forms.ModelForm):
    
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