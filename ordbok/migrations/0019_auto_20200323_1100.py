# Generated by Django 3.0.3 on 2020-03-23 11:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ordbok', '0018_begrepp_externt_register'),
    ]

    operations = [
        migrations.CreateModel(
            name='VisaÄrende',
            fields=[
            ],
            options={
                'verbose_name_plural': 'Kommenterade begrepp',
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('ordbok.opponerabegreppdefinition',),
        ),
        migrations.AlterModelOptions(
            name='opponerabegreppdefinition',
            options={},
        ),
        migrations.AddField(
            model_name='begrepp',
            name='alternativ_definition',
            field=models.TextField(null=True),
        ),
    ]
