from django.contrib import admin
from django.db import models
from pdb import set_trace
from django.conf import settings
from simple_history.models import HistoricalRecords
from django.contrib.auth.models import User, Group
from django.core.exceptions import ValidationError


DEFAULT_STATUS = "Ej Påbörjad"

CONCEPT_STATUS = (('Avråds', "Avråds"),
                  ('Beslutad', 'Beslutad'),
                  ('Pågår', 'Pågår'))

STATUS_VAL = (('Avråds', "Avråds"),
              ('Avställd', "Avställd"),
              ('Beslutad', 'Beslutad'), 
              ('Publicera ej', 'Publicera ej'),
              ('Pågår', 'Pågår'), 
              (DEFAULT_STATUS, DEFAULT_STATUS))

SYSTEM_VAL = (('Millennium', "Millennium"),
              ('Annat system', "Annat system"),
              ('VGR Begreppsystem',"VGR Begreppsystem"))

class Dictionary(models.Model):

    """The dictionary that a term belongs to. The same term can belong
    to more than one dictionary"""
    
    class Meta:     
        verbose_name_plural = "Ordböcker"
        app_label = 'ordbok'

    dictionary_id = models.AutoField(primary_key=True)
    dictionary_context = models.TextField(blank=True, null=True)
    dictionary_name = models.CharField(max_length=50)
    dictionary_long_name = models.CharField(max_length=255, null=True)
    groups = models.ManyToManyField(Group, related_name='dictionaries', blank=True)
    order = models.IntegerField(null=True)

    def __str__(self):
        """Return the name of the domain"""
        return self.dictionary_name

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
    beställare = models.ForeignKey('Bestallare', to_field='id', on_delete=models.CASCADE, related_name="begrepp", null=True, blank=True)
    definition = models.TextField(blank=True)
    tidigare_definition_och_källa = models.TextField(blank=True, null=True)
    externt_id = models.CharField(max_length=255, null=True, verbose_name="Kod", blank=True)
    källa = models.CharField(max_length=255, null=True, blank=True)
    annan_ordlista = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(max_length=255, choices=STATUS_VAL, default=DEFAULT_STATUS)
    term = models.CharField(max_length=255, default='Angavs ej')
    plural = models.CharField(max_length=10, null=True, blank=True)
    utländsk_term = models.CharField(max_length=255, blank=True)
    id_vgr = models.CharField(max_length=255, null=True, blank=True)
    anmärkningar = models.TextField(null=True, blank=True)
    kommentar_handläggning = models.TextField(null=True, blank=True)
    term_i_system = models.CharField(verbose_name="Används i system",max_length=255,blank=True,null=True, choices=SYSTEM_VAL)
    link = models.URLField(help_text="Länk till externt dokument", verbose_name='Länk till begreppsutredning', null=True, blank=True)
    history = HistoricalRecords('datum_skapat')

    dictionaries = models.ManyToManyField(Dictionary, related_name='begrepp')


    def __str__(self):

        """Return the actual term
        """
        return self.term

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

class Synonym(models.Model):

    """The model containings synonyms
    """

    SYNONYM_STATUS =  (('Avråds', "Avråds"),
                       ('Tillåten', "Tillåten"),
                       ('Inte angiven','Inte angiven'))

    class Meta:
        verbose_name_plural = "Synonymer"
        app_label = 'ordbok'

    begrepp = models.ForeignKey("Begrepp", to_field="id", on_delete=models.CASCADE, blank=True, null=True, related_name="legacy_synonyms")
    concept = models.ForeignKey("Concept", to_field="id", on_delete=models.CASCADE, blank=True, null=True, related_name="synonyms")
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
    
    def __str__(self):

        """Retrun the term that is the synonym"""
        return f"{self.begrepp} den {self.datum} av {self.namn}" 

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
    
class ConfigurationOptions(models.Model):

    class Meta:
        verbose_name = ('Inställningar')
        verbose_name_plural = "Inställningar"
        app_label = 'ordbok'
    
    name = models.CharField(max_length=255)     
    description = models.TextField()
    visible = models.BooleanField()
    config = models.JSONField(blank=True, null=True)

    def __str__(self):
        return self.name
    
# Word Model (Core Entity)
class Concept(models.Model):
    term = models.CharField(max_length=255)  # The word itself
    definition = models.TextField()  # Primary definition
    status = models.CharField(choices=CONCEPT_STATUS, max_length=15, null=True)
    changed_at = models.DateTimeField(null=True, auto_now=True, verbose_name='Senaste ändring')
    created_at = models.DateTimeField(null=True, auto_now_add=True, verbose_name='Datum skapat')
    field_positions = models.JSONField(default=dict, null=True, blank=True)

    dictionaries = models.ManyToManyField(Dictionary, related_name='concept')


    def __str__(self):
        return self.term
    
    def get_ordered_fields(self):
        # Default field order with fallback positions
        default_fields = {
            'status': {'display_name': 'Status', 'position': 0},
            'definition': {'display_name': 'Definition', 'position': 1},
        }
        # Merge defaults with custom positions
        for field, meta in self.field_positions.items():
            if field in default_fields:
                default_fields[field]['position'] = meta.get('position', default_fields[field]['position'])
        # Return sorted fields
        return sorted(default_fields.items(), key=lambda x: x[1]['position'])


# Attribute Model
class Attribute(models.Model):
    name = models.CharField(max_length=255)
    display_name = models.CharField(max_length=255)
    data_type = models.CharField(max_length=50, choices=[
        ('string', 'String'),
        ('integer', 'Integer'),
        ('decimal', 'Decimal'),
        ('boolean', 'Boolean'),
        ('text', 'Text'),
        ('url', 'URL'),
    ])
    description = models.TextField(null=True, blank=True)
    position = models.PositiveIntegerField(default=0, null=True, blank=True)


    def __str__(self):
        return self.name

# Attribute Value Model
class AttributeValue(models.Model):
    term = models.ForeignKey(Concept, on_delete=models.CASCADE, related_name='attributes')
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE)
    value_string = models.CharField(max_length=255, null=True, blank=True)
    value_text = models.TextField(null=True, blank=True)
    value_integer = models.IntegerField(null=True, blank=True)
    value_decimal = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    value_boolean = models.BooleanField(null=True, blank=True)
    value_url = models.URLField(null=True, blank=True)

    def clean(self):
        """Ensure only one value field is populated."""
        value_fields = [
            self.value_string,
            self.value_text,
            self.value_integer,
            self.value_decimal,
            self.value_boolean,
            self.value_url,
        ]
        populated_fields = [field for field in value_fields if field not in [None, ""]]
        if len(populated_fields) > 1:
            raise ValidationError("Only one value field can contain data.")
    


    def get_value(self):
        if self.attribute.data_type == 'string':
            return self.value_string
        elif self.attribute.data_type == 'text':
            return self.value_text
        elif self.attribute.data_type == 'url':
            return self.value_url
        elif self.attribute.data_type == 'integer':
            return self.value_integer
        elif self.attribute.data_type == 'decimal':
            return self.value_decimal
        elif self.attribute.data_type == 'boolean':
            return self.value_boolean
        return 
    get_value.short_description = "Värde"


# Business Unit Model
class BusinessUnit(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

# Business Unit Attributes
class BusinessUnitAttribute(models.Model):
    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.CASCADE)
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE)
