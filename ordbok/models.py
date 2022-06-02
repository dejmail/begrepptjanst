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
        verbose_name_plural = "Ordlista"
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

    begrepp_kontext = models.TextField(default='Inte definierad')
    senaste_ändring = models.DateTimeField(auto_now=True, verbose_name='Senaste ändring')
    datum_skapat = models.DateTimeField(auto_now_add=True, verbose_name='Datum skapat')
    beställare = models.ForeignKey('Bestallare', to_field='id', on_delete=models.CASCADE)
    definition = models.TextField(blank=True)
    tidigare_definition_och_källa = models.TextField(blank=True, null=True)
    externt_id = models.CharField(max_length=255, null=True, verbose_name="Kod")
    källa = models.CharField(max_length=255, null=True)
    annan_ordlista = models.CharField(max_length=255, null=True)
    status = models.CharField(max_length=255, choices=STATUS_VAL, default=DEFAULT_STATUS)
    term = models.CharField(max_length=255, default='Angavs ej')
    plural = models.CharField(max_length=10, null=True)
    utländsk_term = models.CharField(max_length=255, blank=True)
    id_vgr = models.CharField(max_length=255, null=True)
    anmärkningar = models.TextField(null=True)
    kommentar_handläggning = models.TextField(null=True)
    term_i_system = models.CharField(verbose_name="Används i system",max_length=255,blank=True,null=True, choices=SYSTEM_VAL)
    usage_recommendation = models.CharField(max_length=50, null=True)

    dictionaries = models.ManyToManyField(Dictionary)
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

    from_term = models.ForeignKey(to="Begrepp", to_field="id", on_delete=models.CASCADE, related_name='from_term')
    to_term = models.ForeignKey(to="Begrepp", to_field="id", on_delete=models.CASCADE, related_name="to_term")
    relationship = models.ForeignKey(to="TypeOfRelationship", to_field="id", on_delete=models.CASCADE)

    def __str__(self) -> str:

        return f"{self.to_term.term},{self.relationship},{self.from_term.term}"

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

class Doman(models.Model):

    """The domain that the term belongs to"""
    
    class Meta:     
        verbose_name_plural = "Domäner"
        app_label = 'ordbok'

    begrepp = models.ForeignKey("Begrepp", to_field="id", on_delete=models.CASCADE, blank=True, null=True, related_name='begrepp_fk')
    domän_id = models.AutoField(primary_key=True)
    domän_kontext = models.TextField(blank=True, null=True)
    domän_namn = models.CharField(max_length=255)

    def __str__(self):

        """Return the name of the domain"""
        return self.domän_namn

class Synonym(models.Model):

    """The model containings synonyms
    """

    SYNONYM_STATUS =  (('Avråds', "Avråds"),
                       ('Tillåten', "Tillåten"),
                       ('Inte angiven','Inte angiven'))

    class Meta:
        verbose_name_plural = "Synonymer"
        app_label = 'ordbok'

    begrepp = models.ForeignKey("Begrepp", to_field="id", on_delete=models.CASCADE, blank=True, null=True)
    synonym = models.CharField(max_length=255, blank=True, null=True)
    synonym_status = models.CharField(max_length=255, choices=SYNONYM_STATUS, default='Inte angiven')

    history = HistoricalRecords()

    def __str__(self):

        """Retrun the term that is the synonym"""
        return self.synonym

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
    
