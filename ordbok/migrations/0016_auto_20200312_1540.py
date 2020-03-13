# Generated by Django 3.0.3 on 2020-03-12 15:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ordbok', '0015_auto_20200312_1537'),
    ]

    operations = [
        migrations.AlterField(
            model_name='begrepp',
            name='status',
            field=models.CharField(choices=[('Avråds', 'Avråds'), ('Definiera ej', 'Definiera ej'), ('Inte definierad', 'Inte definierad'), ('Klar', 'Klar'), ('Pågår', 'Pågår'), ('Publicera ej', 'Publicera ej'), ('Ej Påbörjad', 'Ej Påbörjad')], default='Ej Påbörjad', max_length=255),
        ),
        migrations.AlterField(
            model_name='opponerabegreppdefinition',
            name='status',
            field=models.CharField(choices=[('Avråds', 'Avråds'), ('Definiera ej', 'Definiera ej'), ('Inte definierad', 'Inte definierad'), ('Klar', 'Klar'), ('Pågår', 'Pågår'), ('Publicera ej', 'Publicera ej'), ('Ej Påbörjad', 'Ej Påbörjad')], default='Ej Påbörjad', max_length=50),
        ),
    ]
