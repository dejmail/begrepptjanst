from django import forms
from .models import Doman, Begrepp
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column
from crispy_forms.layout import Field
from django.core.exceptions import ValidationError
from pdb import set_trace

from .models import STATUS_VAL, DEFAULT_STATUS1

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

class TermRequestForm(forms.Form):

    def clean(self):
        cleaned_data = super().clean()
        workstream = cleaned_data.get("workstream")
        other = cleaned_data.get("other")
        
        if (workstream == 'Övrigt/Annan') and (other is None) or (other == ''):
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

    def not_previously_mentionend_in_workstream(self):
        övrig = self.cleaned_data.get('other')

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
    file_field = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}), label="Bifogar en/flera skärmklipp eller filer som kan hjälp oss", required=False)

class TermRequestTranslateForm(forms.Form):

    def clean(self):
        cleaned_data = super().clean()
        workstream = cleaned_data.get("workstream")
        other = cleaned_data.get("other")

        if (workstream == 'Övrigt/Annan') and (other is None):
        # Only do something if both fields are valid so far.
            raise self.add_error('id_other', "Måste ge var begreppet används om du har valt Övrigt/Annan")

    def clean_name(self):
        return self.cleaned_data.get('namn')

    def clean_begrepp(self):
        if self.cleaned_data.get('begrepp') == '':
            return "[Finns ingen översättning]"
        else:
            return self.cleaned_data.get('begrepp')

    def clean_epost(self):
        return self.cleaned_data.get('epost')

    def clean_kontext(self):
        return self.cleaned_data.get('kontext')

    def clean_not_previously_mentionend_in_workstream(self):
        return self.cleaned_data.get('other')

    def clean_workstream(self):
        return self.cleaned_data.get('workstream')

    def clean_utländsk_term(self):
        return self.cleaned_data.get('utländsk_term')
    
    def clean_status(self):
        return DEFAULT_STATUS1

    

    begrepp = forms.CharField(max_length=254, label="Förslag på svensk begrepp", widget = forms.TextInput, required=False)
    utländsk_term = forms.CharField(max_length=254, label="Engelsk term / Vad det heter i systemet")
    kontext = forms.CharField(widget=forms.Textarea, label="Förklara funktionaliteten:")
    workstream = forms.CharField(label='Ström som rapporterar in systembegrepp', widget=forms.Select(choices=workstream_choices))
    other = forms.CharField(max_length=254, label="Om Övrigt/Annan, kan du specificera", required=False)
    epost =  forms.EmailField(max_length=254, label="E-post")
    status = forms.ChoiceField(widget = forms.HiddenInput, choices=STATUS_VAL, initial=DEFAULT_STATUS1)


class OpponeraTermForm(forms.Form):

    namn = forms.CharField()
    epost = forms.EmailField()
    telefon = forms.CharField(max_length=30, label="Kontakt", widget=forms.TextInput(attrs={'placeholder': "Skypenamn eller telefon"}))
    resonemang = forms.CharField(widget=forms.Textarea, max_length=2000, label='Kommentar')
    term = forms.CharField(widget=forms.HiddenInput())  

class BekräftaTermForm(forms.Form):

    # def clean(self):
    #     cleaned_data = super().clean()
    #     workstream = cleaned_data.get("workstream")
    #     other = cleaned_data.get("other")

    #     if (workstream == 'Övrigt/Annan') and (other is None):
    #     # Only do something if both fields are valid so far.
    #         raise ValidationError(
    #             "Måste ge var begreppet används om du har valt Övrigt/Annan"
    #             )

    term = forms.CharField(widget=forms.HiddenInput())  
    epost = forms.EmailField()
    telefon = forms.CharField(max_length=30, label="Kontakt", widget=forms.TextInput(attrs={'placeholder': "Skypenamn eller telefon"}))
    workstream = forms.CharField(label='Verifierar att begreppet används i:', widget=forms.Select(choices=workstream_choices))
    other = forms.CharField(max_length=254, label="Om Övrigt/Annan, kan du specificera", required=False)
    kontext = forms.CharField(label='Specificera var begreppet används')
