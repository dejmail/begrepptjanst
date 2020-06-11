# Generated by Django 3.0.3 on 2020-06-09 15:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ordbok', '0023_auto_20200421_1539'),
    ]

    operations = [
        migrations.AlterField(
            model_name='begrepp',
            name='externt_id',
            field=models.CharField(default='Inte definierad', max_length=255, null=True, verbose_name='Kod'),
        ),
        migrations.AlterField(
            model_name='begrepp',
            name='status',
            field=models.CharField(choices=[('Avråds', 'Avråds'), ('Definiera ej', 'Definiera ej'), ('Inte definierad', 'Inte definierad'), ('Beslutad', 'Beslutad'), ('Pågår', 'Pågår'), ('Publicera ej', 'Publicera ej'), ('Preliminär', 'Preliminär'), ('Ej Påbörjad', 'Ej Påbörjad')], default='Ej Påbörjad', max_length=255),
        ),
        migrations.AlterField(
            model_name='begrepp',
            name='term',
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name='opponerabegreppdefinition',
            name='status',
            field=models.CharField(choices=[('Avråds', 'Avråds'), ('Definiera ej', 'Definiera ej'), ('Inte definierad', 'Inte definierad'), ('Beslutad', 'Beslutad'), ('Pågår', 'Pågår'), ('Publicera ej', 'Publicera ej'), ('Preliminär', 'Preliminär'), ('Ej Påbörjad', 'Ej Påbörjad')], default='Ej Påbörjad', max_length=50),
        ),
    ]