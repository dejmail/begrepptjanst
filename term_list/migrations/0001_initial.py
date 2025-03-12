# Generated by Django 5.1.4 on 2025-03-11 10:12

import django.db.models.deletion
import simple_history.models
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Concept',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('term', models.CharField(max_length=255)),
                ('definition', models.TextField(null=True)),
                ('status', models.CharField(choices=[('Avråds', 'Avråds'), ('Beslutad', 'Beslutad'), ('Pågår', 'Pågår')], max_length=15, null=True)),
                ('changed_at', models.DateTimeField(auto_now=True, null=True, verbose_name='Senaste ändring')),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True, verbose_name='Datum skapat')),
            ],
            options={
                'verbose_name': 'Begrepp',
                'verbose_name_plural': 'Begrepp',
            },
        ),
        migrations.CreateModel(
            name='ConfigurationOptions',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('description', models.TextField()),
                ('visible', models.BooleanField()),
                ('config', models.JSONField(blank=True, null=True)),
            ],
            options={
                'verbose_name': 'Inställningar',
                'verbose_name_plural': 'Inställningar',
            },
        ),
        migrations.CreateModel(
            name='MetadataSearchTrack',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sök_term', models.CharField(max_length=255)),
                ('ip_adress', models.GenericIPAddressField()),
                ('sök_timestamp', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Sök Metadata',
                'verbose_name_plural': 'Sök Metadata',
            },
        ),
        migrations.CreateModel(
            name='SearchTrack',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sök_term', models.CharField(max_length=255)),
                ('ip_adress', models.GenericIPAddressField()),
                ('sök_timestamp', models.DateTimeField(auto_now_add=True)),
                ('records_returned', models.TextField()),
            ],
            options={
                'verbose_name_plural': 'Sök data',
            },
        ),
        migrations.CreateModel(
            name='TaskOrderer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=255)),
                ('create_date', models.DateTimeField(auto_now_add=True)),
                ('finished_by_date', models.DateTimeField(blank=True, null=True)),
                ('email', models.EmailField(max_length=254)),
            ],
            options={
                'verbose_name_plural': 'Beställare',
            },
        ),
        migrations.CreateModel(
            name='Attribute',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('display_name', models.CharField(max_length=255)),
                ('data_type', models.CharField(choices=[('string', 'String'), ('integer', 'Integer'), ('decimal', 'Decimal'), ('boolean', 'Boolean'), ('text', 'Text'), ('url', 'URL')], max_length=50)),
                ('description', models.TextField(blank=True, null=True)),
                ('groups', models.ManyToManyField(blank=True, related_name='attributes', to='auth.group')),
            ],
            options={
                'verbose_name': 'Attribut',
                'verbose_name_plural': 'Attribut',
            },
        ),
        migrations.CreateModel(
            name='AttributeValue',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value_string', models.CharField(blank=True, max_length=255, null=True)),
                ('value_text', models.TextField(blank=True, null=True)),
                ('value_integer', models.IntegerField(blank=True, null=True)),
                ('value_decimal', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('value_boolean', models.BooleanField(blank=True, null=True)),
                ('value_url', models.URLField(blank=True, null=True)),
                ('attribute', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='term_list.attribute')),
                ('term', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attributes', to='term_list.concept')),
            ],
            options={
                'verbose_name': 'Attribut Värde',
                'verbose_name_plural': 'Attribut Värden',
            },
        ),
        migrations.CreateModel(
            name='ConceptComment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('usage_context', models.TextField()),
                ('date', models.DateTimeField(auto_now_add=True)),
                ('email', models.EmailField(max_length=254)),
                ('name', models.CharField(max_length=255)),
                ('status', models.CharField(choices=[('Avråds', 'Avråds'), ('Avställd', 'Avställd'), ('Beslutad', 'Beslutad'), ('Publicera ej', 'Publicera ej'), ('Pågår', 'Pågår'), ('Ej Påbörjad', 'Ej Påbörjad')], default='Ej Påbörjad', max_length=50)),
                ('concept', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='term_list.concept')),
            ],
            options={
                'verbose_name_plural': 'Kommenterade Begrepp',
            },
        ),
        migrations.CreateModel(
            name='ConceptExternalFiles',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('support_file', models.FileField(blank=True, null=True, upload_to='')),
                ('comment', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='term_list.conceptcomment')),
                ('concept', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='term_list.concept')),
            ],
            options={
                'verbose_name_plural': 'Uppladdade filer',
            },
        ),
        migrations.CreateModel(
            name='Dictionary',
            fields=[
                ('dictionary_id', models.AutoField(primary_key=True, serialize=False)),
                ('dictionary_context', models.TextField(blank=True, null=True)),
                ('dictionary_name', models.CharField(max_length=50)),
                ('dictionary_long_name', models.CharField(max_length=255, null=True)),
                ('order', models.IntegerField(null=True)),
                ('groups', models.ManyToManyField(blank=True, related_name='dictionaries', to='auth.group')),
            ],
            options={
                'verbose_name': 'Ordbok',
                'verbose_name_plural': 'Ordböcker',
            },
        ),
        migrations.AddField(
            model_name='concept',
            name='dictionaries',
            field=models.ManyToManyField(related_name='concept', to='term_list.dictionary'),
        ),
        migrations.CreateModel(
            name='GroupHierarchy',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('child', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='parent_groups', to='auth.group')),
                ('parent', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='subgroups', to='auth.group')),
            ],
            options={
                'verbose_name': 'Grupp Hierarki',
                'verbose_name_plural': 'Grupp Hierarki',
            },
        ),
        migrations.CreateModel(
            name='HistoricalAttributeValue',
            fields=[
                ('id', models.IntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('value_string', models.CharField(blank=True, max_length=255, null=True)),
                ('value_text', models.TextField(blank=True, null=True)),
                ('value_integer', models.IntegerField(blank=True, null=True)),
                ('value_decimal', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('value_boolean', models.BooleanField(blank=True, null=True)),
                ('value_url', models.URLField(blank=True, null=True)),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField()),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('attribute', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='term_list.attribute')),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('term', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='term_list.concept')),
            ],
            options={
                'verbose_name': 'historical Attribut Värde',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': 'history_date',
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name='HistoricalConcept',
            fields=[
                ('id', models.IntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('term', models.CharField(max_length=255)),
                ('definition', models.TextField(null=True)),
                ('status', models.CharField(choices=[('Avråds', 'Avråds'), ('Beslutad', 'Beslutad'), ('Pågår', 'Pågår')], max_length=15, null=True)),
                ('changed_at', models.DateTimeField(blank=True, editable=False, null=True, verbose_name='Senaste ändring')),
                ('created_at', models.DateTimeField(blank=True, editable=False, null=True, verbose_name='Datum skapat')),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField()),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'historical Begrepp',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': 'history_date',
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name='HistoricalSynonym',
            fields=[
                ('id', models.IntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('synonym', models.CharField(blank=True, max_length=255, null=True)),
                ('synonym_status', models.CharField(choices=[('Avråds', 'Avråds'), ('Tillåten', 'Tillåten'), ('Inte angiven', 'Inte angiven')], default='Inte angiven', max_length=255)),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField()),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('concept', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='term_list.concept')),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'historical Synonym',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': 'history_date',
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name='Synonym',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('synonym', models.CharField(blank=True, max_length=255, null=True)),
                ('synonym_status', models.CharField(choices=[('Avråds', 'Avråds'), ('Tillåten', 'Tillåten'), ('Inte angiven', 'Inte angiven')], default='Inte angiven', max_length=255)),
                ('concept', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='synonyms', to='term_list.concept')),
            ],
            options={
                'verbose_name': 'Synonym',
                'verbose_name_plural': 'Synonymer',
            },
        ),
        migrations.CreateModel(
            name='GroupAttribute',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('position', models.PositiveIntegerField(default=0)),
                ('attribute', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='term_list.attribute')),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='auth.group')),
            ],
            options={
                'verbose_name': 'Attribut Grupp',
                'verbose_name_plural': 'Attribut Grupper',
                'unique_together': {('group', 'attribute')},
            },
        ),
    ]
