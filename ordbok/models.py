from django.contrib import admin
from django.db import models

# Create your models here.
 
class Begrepp(models.Model):

    class Meta:
        verbose_name_plural = "Begrepp"

    DEFAULT_STATUS = 'Ny'
    STATUS_VAL = (
        'Avråds' : 'Avråds'
        'Definiera ej' : 'Definiera ej', 
        'Inte definierad' : 'Inte definierad', 
        'Klar' : 'Klar', 
        DEFAULT_STATUS : DEFAULT_STATUS, 
        'Pågår' : 'Pågår', 
        'Publicera ej' : 'Publicera ej'        
    )

    begrepp_kontext = models.TextField()
    begrepp_version_nummer = models.DateField()
    beställare_id = models.ForeignKey("Bestallare", on_delete=models.CASCADE)
    definition = models.TextField()
    externt_id = models.CharField(max_length=255)
    externt_register = models.CharField(max_length=255)
    status = models.CharField(max_length=255,choices=STATUS_VAL,default=DEFAULT_STATUS)
    synonym = models.ManCharField(max_length=255)
    term = models.CharField(max_length=255)
    utländsk_definition = models.TextField()
    utländsk_term = models.CharField(max_length=255)
    vgr_id = models.CharField(max_length=255)

class Bestallare(models.Model):
    class Meta:
        verbose_name_plural = "Beställare"

    beställare_namn = models.CharField(max_length=255)
    beställare_datum = models.DateField()
    beställare_email = models.EmailField()
    beställare_telefon = models.IntegerField()
    domän = models.ForeignKey("Doman", to_field='domän_id', on_delete=models.PROTECT, blank=True, null=True)

class Doman(models.Model):
        class Meta:
        verbose_name_plural = "Domäner"

    domän_id = models.CharField(max_length=255, primary_key=True)
    domän_namn = models.CharField(max_length=255)
    domän_email = models.CharField(max_length=255)

class Synonym(models.Model):

        class Meta:
        verbose_name_plural = "Synonymer"

    synonym_id = models.IntegerField(primary_key=True)
    synonym = models.CharField(max_length=255)
