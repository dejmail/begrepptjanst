from django.contrib import admin
from django.db import models

DEFAULT_STATUS = "Ej Påbörjad"

STATUS_VAL = (('Avråds', "Avråds"),
              ('Definiera ej', 'Definiera ej'), 
              ('Inte definierad', 'Inte definierad'), 
              ('Klar', 'Klar'), 
              ('Pågår', 'Pågår'), 
              ('Publicera ej', 'Publicera ej'),
              (DEFAULT_STATUS, DEFAULT_STATUS))

class Begrepp(models.Model):

    class Meta:
        verbose_name_plural = "Begrepp"

    begrepp_kontext = models.TextField()
    begrepp_version_nummer = models.DateTimeField()
    beställare = models.ForeignKey('Bestallare', to_field='id', on_delete=models.CASCADE)
    definition = models.TextField()
    externt_id = models.CharField(max_length=255, null=True)
    externt_register = models.CharField(max_length=255, null=True)
    status = models.CharField(max_length=255, choices=STATUS_VAL, default=DEFAULT_STATUS)
    term = models.CharField(max_length=255)
    utländsk_definition = models.TextField(default='Inte definierad')
    utländsk_term = models.CharField(default='Inte definierad', max_length=255)
    vgr_id = models.CharField(max_length=255, null=True)
    anmärkningar = models.TextField()
    kommentar_handläggning = models.TextField()


    def __str__(self):
        return self.term

class Bestallare(models.Model):
    class Meta:
        verbose_name_plural = "Beställare"

    beställare_namn = models.CharField(max_length=255)
    beställare_datum = models.DateTimeField()
    beställare_email = models.EmailField()
    beställare_telefon = models.IntegerField()

    def __str__(self):
        return self.beställare_namn

class Doman(models.Model):
    class Meta:     
        verbose_name_plural = "Domäner"

    begrepp = models.ForeignKey("Begrepp", to_field="id", on_delete=models.PROTECT, blank=True, null=True)
    domän_id = models.AutoField(primary_key=True)
    domän_kontext = models.TextField()
    domän_namn = models.CharField(max_length=255)       

    def __str__(self):
        return self.domän_namn

class Synonym(models.Model):

    class Meta:
        verbose_name_plural = "Synonymer"

    begrepp = models.ForeignKey("Begrepp", to_field="id", on_delete=models.PROTECT, blank=True, null=True)
    synonym = models.CharField(max_length=255)
    synonym_status = models.CharField(max_length=255, choices=STATUS_VAL, default=DEFAULT_STATUS)

    def __str__(self):
        return self.synonym

class OpponeraBegreppDefinition(models.Model):

    class Meta:
        verbose_name_plural = 'Ifrågasatt Begrepp Definitioner'
    
    begrepp = models.ForeignKey("Begrepp", to_field="id", on_delete=models.PROTECT, blank=True, null=True)
    begrepp_kontext = models.TextField()
    datum = models.DateTimeField()
    epost = models.EmailField()
    namn = models.CharField(max_length=255)
    status = models.CharField(max_length=50, choices=STATUS_VAL, default=DEFAULT_STATUS)
    telefon = models.CharField(max_length=13)