from django import forms
from .models import Doman, Begrepp

workstream_choices = [('Ordination & Beställningar','Ordination & Beställningar'),
                        ('Akutsjukvård','Akutsjukvård'),
                        ('Dokumentation Vårdproffesion','Dokumentation Vårdproffesion'),
                        ('Kärnfunktioner','Kärnfunktioner'),
                        ('Materiallogistik','Materiallogistik'),
                        ('Medicinsk Dokumentation','Medicinsk Dokumentation'),
                        ('Mödravård Obstetrik','Mödravård Obstetrik'),
                        ('Onkologi','Onkologi'),
                        ('Operation','Operation'),
                        ('PAS','PAS'),
                        ('Primärvård','Primärvård'),
                        ('Psykiatri','Psykiatri'),
                        ('Rapporter','Rapporter')]

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

    namn = forms.CharField(max_length=100)
    epost =  forms.EmailField(max_length=254)
    mobil_telefon = forms.IntegerField()
    begrepp = forms.CharField(max_length=254)    
    #workstream = forms.ModelChoiceField(queryset=Doman.objects.all().order_by('domän_namn').values_list('domän_namn', flat=True).distinct())
    workstream = forms.CharField(label='Välja arbetsström', widget=forms.Select(choices=workstream_choices))
    kontext = forms.CharField(widget=forms.Textarea)
    workflow_namn = forms.CharField(max_length=254)

class OpponeraTermForm(forms.Form):

    namn = forms.CharField()
    epost = forms.EmailField()
    telefon = forms.CharField(max_length=20)
    resonemang = forms.CharField(widget=forms.Textarea, max_length=2000, label='Kommentar')
    term = forms.CharField(widget=forms.HiddenInput())  

class BekräftaTermForm(forms.Form):

    term = forms.CharField(widget=forms.HiddenInput())  
    epost = forms.EmailField()
    kontext = forms.CharField(label='WDPW Acitivity ID / Dokument Kontext')
    workstream = forms.CharField(label='Välja arbetsström', widget=forms.Select(choices=workstream_choices))
