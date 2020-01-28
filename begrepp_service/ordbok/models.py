from django.db import models
from django.contrib import admin

# Create your models here.
 
class Begrepp(models.Model):
    begrepp_key = models.IntegerField(primary_key=True)
    beställare_id = models.ForeignKey("Beställare", on_delete=models.CASCADE)
    definition = models.TextField()
    kontext_beskrivning = models.TextField()
    synonym = models.CharField(max_length=255)
    term = models.CharField(max_length=255)
    utländsk_definition = models.TextField()
    utländsk_term = models.CharField(max_length=255)
    begrepp_version_nummer = models.IntegerField()

class Beställare(models.Model):
    beställare_datum = models.DateField()
    beställare_email = models.EmailField()
    beställare_kontext = models.CharField(max_length=255)
    beställare_namn = models.CharField(max_length=255)
    beställare_telefon = models.IntegerField()
    domain_id = models.CharField(max_length=255)

class Domän(models.Model):
    domain_id = models.ForeignKey('Beställare', on_delete=models.CASCADE)
    domän_namn = models.CharField(max_length=255)
    domän_email = models.CharField(max_length=255)

