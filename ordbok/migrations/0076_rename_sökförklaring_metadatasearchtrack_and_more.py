# Generated by Django 5.1.3 on 2024-12-04 12:09

import django.db.models.deletion
import simple_history.models
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ordbok', '0075_concept_field_positions_alter_concept_changed_at_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RenameModel(
            old_name='SökFörklaring',
            new_name='MetadataSearchTrack',
        ),
        migrations.RenameModel(
            old_name='SökData',
            new_name='SearchTrack',
        ),
        migrations.RenameModel(
            old_name='Bestallare',
            new_name='TaskOrderer',
        ),
        migrations.AlterField(
            model_name='synonym',
            name='concept',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='synonyms', to='ordbok.concept'),
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
                ('telephone', models.CharField(max_length=30)),
                ('concept', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='ordbok.concept')),
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
                ('comment', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='ordbok.conceptcomment')),
                ('concept', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='ordbok.concept')),
            ],
            options={
                'verbose_name_plural': 'Uppladdade filer',
            },
        ),
        migrations.CreateModel(
            name='HistoricalConcept',
            fields=[
                ('id', models.IntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('term', models.CharField(max_length=255)),
                ('definition', models.TextField()),
                ('status', models.CharField(choices=[('Avråds', 'Avråds'), ('Beslutad', 'Beslutad'), ('Pågår', 'Pågår')], max_length=15, null=True)),
                ('changed_at', models.DateTimeField(blank=True, editable=False, null=True, verbose_name='Senaste ändring')),
                ('created_at', models.DateTimeField(blank=True, editable=False, null=True, verbose_name='Datum skapat')),
                ('field_positions', models.JSONField(blank=True, default=dict, null=True)),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField()),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'datum_skapat',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': 'history_date',
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
    ]
