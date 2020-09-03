from django import forms
from .models import Doman, Begrepp
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column
from crispy_forms.layout import Field

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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'begrepp',
            'kontext',
            'workstream',
            'other'
            'namn',
            'epost',
            'telefon',
            Row('skärmbild', css_class='btn btn-default btn-file'),
            CustomScreencast('Skapa en screencast med audio'),
            Submit('submit', 'Sign in')
        )

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

    def not_previously_mentionend_in_workstream(self):
        övrig = self.cleaned_data.get('other')

    begrepp = forms.CharField(max_length=254, label="Term som representerar begreppet", widget = forms.TextInput)
    kontext = forms.CharField(widget=forms.Textarea, label="Beskriv hur begreppet används:")
    workstream = forms.CharField(label='Var används begreppet', widget=forms.Select(choices=workstream_choices))
    other = forms.CharField(max_length=254, label="Om Övrigt/Annan, kan du specificera", required=False)
    önskad_datum = forms.DateField(widget=CustomDateInput, label="Önskad slutdatum för prioritering", help_text="Klicka på kalendar ikon på höger sidan")
    namn = forms.CharField(max_length=100)
    epost =  forms.EmailField(max_length=254, label="E-post")
    telefon = forms.CharField(max_length=30, label="Kontakt",  widget=forms.TextInput(attrs={'placeholder': "Skypenamn eller telefon"})) 
    file_field = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}), required=False)

class CustomScreencast(Field):
    template = 'custom_screencast.html'
    

class OpponeraTermForm(forms.Form):

    namn = forms.CharField()
    epost = forms.EmailField()
    telefon = forms.CharField(max_length=30, label="Kontakt", widget=forms.TextInput(attrs={'placeholder': "Skypenamn eller telefon"}))
    resonemang = forms.CharField(widget=forms.Textarea, max_length=2000, label='Kommentar')
    term = forms.CharField(widget=forms.HiddenInput())  

class BekräftaTermForm(forms.Form):

    term = forms.CharField(widget=forms.HiddenInput())  
    epost = forms.EmailField()
    telefon = forms.CharField(max_length=30, label="Kontakt", widget=forms.TextInput(attrs={'placeholder': "Skypenamn eller telefon"}))
    workstream = forms.CharField(label='Verifierar att begreppet används i:', widget=forms.Select(choices=workstream_choices))
    kontext = forms.CharField(label='Specificera var begreppet används')
