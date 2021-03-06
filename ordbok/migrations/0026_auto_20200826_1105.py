# Generated by Django 3.0.3 on 2020-08-26 11:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ordbok', '0025_auto_20200713_0858'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='sökförklaring',
            options={'verbose_name': 'Sök Förklaring'},
        ),
        migrations.AlterField(
            model_name='begrepp',
            name='begrepp_version_nummer',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Senaste ändring'),
        ),
        migrations.AlterField(
            model_name='bestallare',
            name='beställare_telefon',
            field=models.CharField(max_length=30),
        ),
        migrations.AlterField(
            model_name='opponerabegreppdefinition',
            name='telefon',
            field=models.CharField(max_length=30),
        ),
    ]
