from django import forms
from .models import Doman, Begrepp

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


class TermRequestForm(forms.Form):

    def clean_name(self):
        namn =  self.cleaned_data.get('namn')
        return namn

    def clean_epost(self):
        epost = self.cleaned_data.get('epost')
        return epost
    
    def clean_telefon(self):
        telefon = self.cleaned_data.get('mobil_telefon')
        return telefon

    def not_previously_mentionend_in_workstream(self):
        övrig = self.cleaned_data.get('other')

    namn = forms.CharField(max_length=100)
    epost =  forms.EmailField(max_length=254, label="E-post")
    telefon = forms.CharField(max_length=20, label="Telefon")
    begrepp = forms.CharField(max_length=254, label="Term som representerar begreppet")
    workstream = forms.CharField(label='Välj workstream', widget=forms.Select(choices=workstream_choices))
    other = forms.CharField(max_length=254, label="Om Övrigt/Annan, kan du specificera", required=False)
    kontext = forms.CharField(widget=forms.Textarea, label="Begreppskontext")
    workflow_namn = forms.CharField(max_length=254)

class OpponeraTermForm(forms.Form):

    namn = forms.CharField()
    epost = forms.EmailField()
    telefon = forms.CharField(max_length=20, label="telefon")
    resonemang = forms.CharField(widget=forms.Textarea, max_length=2000, label='Kommentar')
    term = forms.CharField(widget=forms.HiddenInput())  

class BekräftaTermForm(forms.Form):

    term = forms.CharField(widget=forms.HiddenInput())  
    epost = forms.EmailField()
    telefon = forms.CharField(max_length=20, label="telefon")
    workstream = forms.CharField(label='Verifierar att begreppet används i:', widget=forms.Select(choices=workstream_choices))
    kontext = forms.CharField(label='Verifierad användning')
