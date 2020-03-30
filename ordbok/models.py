from django.contrib import admin
from django.db import models
from pdb import set_trace

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

    begrepp_kontext = models.TextField(default='Inte definierad')
    begrepp_version_nummer = models.DateTimeField()
    beställare = models.ForeignKey('Bestallare', to_field='id', on_delete=models.CASCADE)
    definition = models.TextField()
    alternativ_definition = models.TextField(null=True)
    externt_id = models.CharField(max_length=255, null=True, default='Inte definierad')
    källa = models.CharField(max_length=255, null=True, default='Inte definierad')
    externt_register = models.CharField(max_length=255, null=True, default='Inte definierad')
    status = models.CharField(max_length=255, choices=STATUS_VAL, default=DEFAULT_STATUS)
    term = models.CharField(max_length=255)
    utländsk_definition = models.TextField(default='Inte definierad')
    utländsk_term = models.CharField(default='Inte definierad', max_length=255)
    id_vgr = models.CharField(max_length=255, null=True, default='Inte definierad')
    anmärkningar = models.TextField(null=True, default='Inte definierad')
    kommentar_handläggning = models.TextField(null=True, default='Inte definierad')


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

    SYNONYM_STATUS =  (('Avråds', "Avråds"),
                       ('Tillåten', "Tillåten"),
                       ('Rekommenderad', "Rekommenderad"),
                       ('Inte angiven','Inte angiven'))

    class Meta:
        verbose_name_plural = "Synonymer"

    begrepp = models.ForeignKey("Begrepp", to_field="id", on_delete=models.PROTECT, blank=True, null=True)
    synonym = models.CharField(max_length=255, blank=True, null=True)
    synonym_status = models.CharField(max_length=255, choices=SYNONYM_STATUS, default='Inte angiven')

    def __str__(self):
        return self.synonym

class OpponeraBegreppDefinition(models.Model):

    class Meta:
        verbose_name_plural = 'Kommenterade Begrepp'
    
    begrepp = models.ForeignKey("Begrepp", to_field="id", on_delete=models.PROTECT, blank=True, null=True)
    begrepp_kontext = models.TextField()
    datum = models.DateTimeField()
    epost = models.EmailField()
    namn = models.CharField(max_length=255)
    status = models.CharField(max_length=50, choices=STATUS_VAL, default=DEFAULT_STATUS)
    telefon = models.CharField(max_length=13)

class SökData(models.Model):

    class Meta:
        verbose_name_plural = 'Sök data'

    sök_term = models.CharField(max_length=255)
    ip_adress = models.GenericIPAddressField()
    sök_timestamp = models.DateTimeField(auto_now_add=True)
    records_returned = models.TextField()

class SökFörklaring(models.Model):

    sök_term = models.CharField(max_length=255)
    ip_adress = models.GenericIPAddressField()
    sök_timestamp = models.DateTimeField(auto_now_add=True)
    
