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

STATUS_CHOICES = (('Avråds', "Avråds"),
              ('Avställd', "Avställd"),
              ('Beslutad', 'Beslutad'), 
              ('Publicera ej', 'Publicera ej'),
              ('Pågår', 'Pågår'), 
              (DEFAULT_STATUS, DEFAULT_STATUS))

class Dictionary(models.Model):

    """The dictionary that a term belongs to. The same term can belong
    to more than one dictionary"""
    
    class Meta:     
        verbose_name_plural = "Ordböcker"
        verbose_name = "Ordbok"
        app_label = 'term_list'

    dictionary_id = models.AutoField(primary_key=True)
    dictionary_context = models.TextField(blank=True, null=True)
    dictionary_name = models.CharField(max_length=50)
    dictionary_long_name = models.CharField(max_length=255, null=True)
    groups = models.ManyToManyField(Group, related_name='dictionaries', blank=True)
    order = models.IntegerField(null=True)

    def __str__(self):
        """Return the name of the domain"""
        return self.dictionary_name

class ConceptExternalFiles(models.Model):

    """When a user requests a new term for definition they are able to upload
    files that give context. Those files are stored in thos model, and each 
    term can have many files connected to it.
    """

    class Meta:
        verbose_name_plural = "Uppladdade filer"
        app_label = 'term_list'

    concept = models.ForeignKey("Concept", to_field='id', on_delete=models.CASCADE)
    comment = models.ForeignKey("ConceptComment", to_field='id', null=True, blank=True, on_delete=models.CASCADE)
    support_file = models.FileField(blank=True, null=True, upload_to='')
    
    def __str__(self):
        
        """Return the name of the file
        """
        return str(self.support_file)

class TaskOrderer(models.Model):

    """The model containing the person who has either submitted a request for
    a new term or has commented on an existing term.
    """

    class Meta:
        verbose_name_plural = "Beställare"
        app_label = 'term_list'

    name = models.CharField(max_length=255, blank=True)
    create_date = models.DateTimeField(auto_now_add=True)
    finished_by_date = models.DateTimeField(null=True, blank=True)
    email = models.EmailField()

    def __str__(self):
        
        """Return the requesters name
        """
        return self.name

class Synonym(models.Model):

    """The model containings synonyms
    """

    SYNONYM_STATUS =  (('Avråds', "Avråds"),
                       ('Tillåten', "Tillåten"),
                       ('Inte angiven','Inte angiven'))

    class Meta:
        verbose_name_plural = "Synonymer"
        verbose_name = "Synonym"
        app_label = 'term_list'

    #begrepp = models.ForeignKey("Begrepp", to_field="id", on_delete=models.CASCADE, blank=True, null=True, related_name="legacy_synonyms")
    concept = models.ForeignKey("Concept", to_field="id", on_delete=models.CASCADE, blank=True, null=True, related_name="synonyms")
    synonym = models.CharField(max_length=255, blank=True, null=True)
    synonym_status = models.CharField(max_length=255, choices=SYNONYM_STATUS, default='Inte angiven')

    history = HistoricalRecords()

    def __str__(self):

        """Retrun the term that is the synonym"""
        return self.synonym

class ConceptComment(models.Model):

    """Model containing comments that are submitted by users against a 
    particular term.
    """

    class Meta:
        verbose_name_plural = 'Kommenterade Begrepp'
        app_label = 'term_list'

    concept = models.ForeignKey("Concept", to_field="id", on_delete=models.CASCADE, blank=True, null=True)
    usage_context = models.TextField()
    date = models.DateTimeField(auto_now_add=True)
    email = models.EmailField()
    name = models.CharField(max_length=255)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default=DEFAULT_STATUS)
    
    def __str__(self):

        """Retrun the term that is the synonym"""
        return f"{self.concept} den {self.date} av {self.name}" 

class SearchTrack(models.Model):

    """Table that collects the IP address, the term search for and the 
    timestamp.
    """

    class Meta:
        verbose_name_plural = 'Sök data'
        app_label = 'term_list'

    sök_term = models.CharField(max_length=255)
    ip_adress = models.GenericIPAddressField()
    sök_timestamp = models.DateTimeField(auto_now_add=True)
    records_returned = models.TextField()

    def __str__(self):
        return self.sök_term

class MetadataSearchTrack(models.Model):

    """Table taking note of which term definitions are clicked on.
    """

    class Meta:
        verbose_name = ('Sök Metadata')
        verbose_name_plural = ('Sök Metadata')
        app_label = 'term_list'

    sök_term = models.CharField(max_length=255)
    ip_adress = models.GenericIPAddressField()
    sök_timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.sök_term
    
class ConfigurationOptions(models.Model):

    class Meta:
        verbose_name = ('Inställningar')
        verbose_name_plural = "Inställningar"
        app_label = 'term_list'
    
    name = models.CharField(max_length=255)     
    description = models.TextField()
    visible = models.BooleanField()
    config = models.JSONField(blank=True, null=True)

    def __str__(self):
        return self.name
    
# Word Model (Core Entity)
class Concept(models.Model):

    class Meta:
        verbose_name = "Begrepp"
        verbose_name_plural = "Begrepp"
        app_label = 'term_list'

    term = models.CharField(max_length=255)  # The word itself
    definition = models.TextField(null=True, blank=True)  # Primary definition
    status = models.CharField(choices=CONCEPT_STATUS, max_length=15, null=True)
    changed_at = models.DateTimeField(null=True, auto_now=True, verbose_name='Senaste ändring')
    created_at = models.DateTimeField(null=True, auto_now_add=True, verbose_name='Datum skapat')
    history = HistoricalRecords(['changed_at', 'definition'])

    dictionaries = models.ManyToManyField(Dictionary, related_name='concept')

    history = HistoricalRecords()

    def __str__(self):
        return self.term
    
    def get_ordered_fields(self):
        # Default field order with fallback positions
        default_fields = {
            'status': {'display_name': 'Status', 'position': 0},
            'definition': {'display_name': 'Definition', 'position': 1},
        }

        return sorted(default_fields.items(), key=lambda x: x[1]['position'])

class GroupAttribute(models.Model):

    class Meta:
        unique_together = ('group', 'attribute')
        verbose_name = "Attribut Grupp"
        verbose_name_plural = "Attribut Grupper"

    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    attribute = models.ForeignKey('Attribute', on_delete=models.CASCADE)
    position = models.PositiveIntegerField(default=0)    

# Attribute Model
class Attribute(models.Model):

    class Meta:
        verbose_name = "Attribut"
        verbose_name_plural = "Attribut"    

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
    groups = models.ManyToManyField(Group, related_name='attributes', blank=True)

    def __str__(self):
        return self.name

# Attribute Value Model
class AttributeValue(models.Model):

    class Meta:
        verbose_name = "Attribut Värde"
        verbose_name_plural = "Attribut Värden"

    term = models.ForeignKey(Concept, on_delete=models.CASCADE, related_name='attributes')
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE)
    value_string = models.CharField(max_length=255, null=True, blank=True)
    value_text = models.TextField(null=True, blank=True)
    value_integer = models.IntegerField(null=True, blank=True)
    value_decimal = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    value_boolean = models.BooleanField(null=True, blank=True)
    value_url = models.URLField(null=True, blank=True)

    history = HistoricalRecords()

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

    def get_attribute_name(self):
        return self.attribute.name
    get_attribute_name.short_description = "Attribute"

    def __str__(self):
        return str(self.attribute_id)


class GroupHierarchy(models.Model):

    class Meta:
        verbose_name = "Grupp Hierarki"
        verbose_name_plural = "Grupp Hierarki"

    parent = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='subgroups')
    child = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='parent_groups')

    def __str__(self):
        return f"{self.child.name} (child of {self.parent.name})"
