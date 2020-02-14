from django import forms

class TermRequestForm(forms.Form):
    begrepp =  forms.CharField(max_length=254)
    first_name =  forms.CharField(max_length=50)
    last_name =  forms.CharField(max_length=50)
    epost =  forms.EmailField(max_length=254)
    mobil_telefon = forms.IntegerField()
    workstream = forms.CharField(max_length=150)
    kontext = forms.CharField(widget=forms.Textarea)
    workflow_name = forms.CharField(max_length=254)