# Generated by Django 4.2.1 on 2023-06-08 12:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ordbok', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='begrepp',
            name='anmärkningar',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='begrepp',
            name='annan_ordlista',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='begrepp',
            name='begrepp_kontext',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='begrepp',
            name='definition',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='begrepp',
            name='externt_id',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Kod'),
        ),
        migrations.AlterField(
            model_name='begrepp',
            name='id_vgr',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='begrepp',
            name='kommentar_handläggning',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='begrepp',
            name='källa',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='begrepp',
            name='plural',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
        migrations.AlterField(
            model_name='begrepp',
            name='status',
            field=models.CharField(blank=True, choices=[('Avråds', 'Avråds'), ('Avställd', 'Avställd'), ('Beslutad', 'Beslutad'), ('Definiera ej', 'Definiera ej'), ('För validering', 'För validering'), ('Internremiss', 'Internremiss'), ('Preliminär', 'Preliminär'), ('Publicera ej', 'Publicera ej'), ('Pågår', 'Pågår'), ('Ej Påbörjad', 'Ej Påbörjad')], default='Ej Påbörjad', max_length=255),
        ),
        migrations.AlterField(
            model_name='begrepp',
            name='term',
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name='begrepp',
            name='usage_recommendation',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='historicalbegrepp',
            name='anmärkningar',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='historicalbegrepp',
            name='annan_ordlista',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='historicalbegrepp',
            name='begrepp_kontext',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='historicalbegrepp',
            name='definition',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='historicalbegrepp',
            name='externt_id',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Kod'),
        ),
        migrations.AlterField(
            model_name='historicalbegrepp',
            name='id_vgr',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='historicalbegrepp',
            name='kommentar_handläggning',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='historicalbegrepp',
            name='källa',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='historicalbegrepp',
            name='plural',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
        migrations.AlterField(
            model_name='historicalbegrepp',
            name='status',
            field=models.CharField(blank=True, choices=[('Avråds', 'Avråds'), ('Avställd', 'Avställd'), ('Beslutad', 'Beslutad'), ('Definiera ej', 'Definiera ej'), ('För validering', 'För validering'), ('Internremiss', 'Internremiss'), ('Preliminär', 'Preliminär'), ('Publicera ej', 'Publicera ej'), ('Pågår', 'Pågår'), ('Ej Påbörjad', 'Ej Påbörjad')], default='Ej Påbörjad', max_length=255),
        ),
        migrations.AlterField(
            model_name='historicalbegrepp',
            name='term',
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name='historicalbegrepp',
            name='usage_recommendation',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]
