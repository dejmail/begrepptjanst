from django.contrib import admin
from django.db import models
from pdb import set_trace
from django.conf import settings
from simple_history.models import HistoricalRecords

DEFAULT_STATUS = "Ej Påbörjad"

STATUS_VAL = (('Avråds', "Avråds"),
              ('Avställd', "Avställd"),
              ('Beslutad', 'Beslutad'), 
              ('Definiera ej', 'Definiera ej'), 
              ('För validering', 'För validering'), 
              ("Internremiss", "Internremiss"), 
              ('Preliminär', 'Preliminär'),
              ('Publicera ej', 'Publicera ej'),
              ('Pågår', 'Pågår'), 
              (DEFAULT_STATUS, DEFAULT_STATUS))

USAGE_RECOMMENDATION = ((),)


SYSTEM_VAL = (('Millennium', "Millennium"),
              ('Annat system', "Annat system"),
              ('VGR Begreppsystem',"VGR Begreppsystem"))


class Dictionary(models.Model):

    """Dictionary model that all terms belong to. The reverse relationship used 
    is ManytoMany as terms can belong to multiple dictionaries.
    """

    class Meta: 
        verbose_name_plural = "Ordlistor"
        app_label = 'ordbok'

    title = models.CharField(max_length=72, default='Main')
    description = models.TextField(max_length=1000, null=True)

    def __str__(self):

        """Return the title of the dictionary
        """
        return self.title


class Begrepp(models.Model):

    """Model that contains all the metadata regarding a term. Model has
    historical copies.
    """

    class Meta:
        verbose_name_plural = "Begrepp"
        app_label = 'ordbok'

    begrepp_kontext = models.TextField(null=True, blank=True)
    senaste_ändring = models.DateTimeField(auto_now=True, verbose_name='Senaste ändring')
    datum_skapat = models.DateTimeField(auto_now_add=True, verbose_name='Datum skapat')
    beställare = models.ForeignKey('Bestallare', to_field='id', on_delete=models.CASCADE)
    definition = models.TextField(blank=True, null=True)
    tidigare_definition_och_källa = models.TextField(blank=True, null=True)
    external_id = models.CharField(max_length=255, null=True, verbose_name="Kod", blank=True)
    källa = models.CharField(max_length=255, null=True, blank=True)
    annan_ordlista = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(max_length=255, choices=STATUS_VAL, default=DEFAULT_STATUS, blank=True)
    term = models.CharField(max_length=255)
    plural = models.CharField(max_length=10, null=True, blank=True)
    utländsk_term = models.CharField(max_length=255, blank=True)
    official_id = models.CharField(max_length=255, null=True, blank=True)
    anmärkningar = models.TextField(null=True, blank=True)
    kommentar_handläggning = models.TextField(null=True, blank=True)
    term_i_system = models.CharField(verbose_name="Används i system",max_length=255,blank=True,null=True, choices=SYSTEM_VAL)
    link = models.URLField(help_text="Länk till externt dokument", verbose_name='Länk till begreppsutredning', null=True, blank=True)
    usage_recommendation = models.CharField(max_length=50, null=True, blank=True)

    dictionaries = models.ManyToManyField(Dictionary, related_name="dictionary_set")
    history = HistoricalRecords('datum_skapat')

    def __str__(self):

        """Return the actual term
        """
        return self.term

class TypeOfRelationship(models.Model):

    relationship = models.CharField(max_length=255)

    def __str__(self):

        return self.relationship

class TermRelationship(models.Model):

    base_term = models.ForeignKey(to="Begrepp", on_delete=models.CASCADE, related_name='base_term', null=True)
    child_term = models.ForeignKey(to="Begrepp", on_delete=models.CASCADE, related_name="child_term", null=True)
    relationship = models.ForeignKey(to="TypeOfRelationship", on_delete=models.CASCADE)

    def __str__(self) -> str:
        #set_trace()
        return f"{self.child_term} är en {self.relationship} {self.base_term}"

class BegreppExternalFiles(models.Model):

    """When a user requests a new term for definition they are able to upload
    files that give context. Those files are stored in thos model, and each 
    term can have many files connected to it.
    """

    class Meta:
        verbose_name_plural = "Uppladdade filer"
        app_label = 'ordbok'

    begrepp = models.ForeignKey("Begrepp", to_field='id', on_delete=models.CASCADE)
    kommentar = models.ForeignKey("KommenteraBegrepp", to_field='id', null=True, blank=True, on_delete=models.CASCADE)
    support_file = models.FileField(blank=True, null=True, upload_to='')
    
    def __str__(self):
        
        """Return the name of the file
        """
        return str(self.support_file)

class Bestallare(models.Model):

    """The model containing the person who has either submitted a request for
    a new term or has commented on an existing term.
    """

    class Meta:
        verbose_name_plural = "Beställare"
        app_label = 'ordbok'

    beställare_namn = models.CharField(max_length=255, blank=True)
    beställare_datum = models.DateTimeField(auto_now_add=True)
    önskad_slutdatum = models.DateTimeField(null=True, blank=True)
    beställare_email = models.EmailField()
    beställare_telefon = models.CharField(max_length=30, blank=True)

    def __str__(self):
        
        """Return the requesters name
        """
        return self.beställare_namn

class KommenteraBegrepp(models.Model):

    """Model containing comments that are submitted by users against a 
    particular term.
    """

    class Meta:
        verbose_name_plural = 'Kommenterade Begrepp'
        app_label = 'ordbok'

    begrepp = models.ForeignKey("Begrepp", to_field="id", on_delete=models.CASCADE, blank=True, null=True)
    begrepp_kontext = models.TextField()
    datum = models.DateTimeField(auto_now_add=True)
    epost = models.EmailField()
    namn = models.CharField(max_length=255)
    status = models.CharField(max_length=50, choices=STATUS_VAL, default=DEFAULT_STATUS)
    telefon = models.CharField(max_length=30)

class SökData(models.Model):

    """Table that collects the IP address, the term search for and the 
    timestamp.
    """

    class Meta:
        verbose_name_plural = 'Sök data'
        app_label = 'ordbok'

    sök_term = models.CharField(max_length=255)
    ip_adress = models.GenericIPAddressField()
    sök_timestamp = models.DateTimeField(auto_now_add=True)
    records_returned = models.TextField()

    def __str__(self):
        return self.sök_term

class SökFörklaring(models.Model):

    """Table taking note of which term definitions are clicked on.
    """

    class Meta:
        verbose_name = ('Sök Förklaring')
        app_label = 'ordbok'

    sök_term = models.CharField(max_length=255)
    ip_adress = models.GenericIPAddressField()
    sök_timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.sök_term