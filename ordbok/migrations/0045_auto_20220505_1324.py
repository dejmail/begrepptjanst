# Generated by Django 3.2.13 on 2022-05-05 13:24

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ordbok', '0044_auto_20220412_2100'),
    ]

    operations = [
        migrations.RenameField(
            model_name='begrepp',
            old_name='begrepp_version_nummer',
            new_name='senaste_ändring',
        ),
        migrations.RenameField(
            model_name='historicalbegrepp',
            old_name='begrepp_version_nummer',
            new_name='senaste_ändring',
        ),
        migrations.AddField(
            model_name='begrepp',
            name='plural',
            field=models.CharField(max_length=10, null=True),
        ),
        migrations.AddField(
            model_name='historicalbegrepp',
            name='plural',
            field=models.CharField(max_length=10, null=True),
        ),
        migrations.AlterField(
            model_name='begrepp',
            name='anmärkningar',
            field=models.TextField(null=True),
        ),
        migrations.AlterField(
            model_name='begrepp',
            name='annan_ordlista',
            field=models.CharField(max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='begrepp',
            name='externt_id',
            field=models.CharField(max_length=255, null=True, verbose_name='Kod'),
        ),
        migrations.AlterField(
            model_name='begrepp',
            name='id_vgr',
            field=models.CharField(max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='begrepp',
            name='kommentar_handläggning',
            field=models.TextField(null=True),
        ),
        migrations.AlterField(
            model_name='begrepp',
            name='källa',
            field=models.CharField(max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='begrepp',
            name='status',
            field=models.CharField(choices=[('Avråds', 'Avråds'), ('Avställd', 'Avställd'), ('Beslutad', 'Beslutad'), ('Definiera ej', 'Definiera ej'), ('För validering', 'För validering'), ('Internremiss', 'Internremiss'), ('Preliminär', 'Preliminär'), ('Publicera ej', 'Publicera ej'), ('Pågår', 'Pågår'), ('Ej Påbörjad', 'Ej Påbörjad')], default='Ej Påbörjad', max_length=255),
        ),
        migrations.AlterField(
            model_name='historicalbegrepp',
            name='anmärkningar',
            field=models.TextField(null=True),
        ),
        migrations.AlterField(
            model_name='historicalbegrepp',
            name='annan_ordlista',
            field=models.CharField(max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='historicalbegrepp',
            name='externt_id',
            field=models.CharField(max_length=255, null=True, verbose_name='Kod'),
        ),
        migrations.AlterField(
            model_name='historicalbegrepp',
            name='id_vgr',
            field=models.CharField(max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='historicalbegrepp',
            name='kommentar_handläggning',
            field=models.TextField(null=True),
        ),
        migrations.AlterField(
            model_name='historicalbegrepp',
            name='källa',
            field=models.CharField(max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='historicalbegrepp',
            name='status',
            field=models.CharField(choices=[('Avråds', 'Avråds'), ('Avställd', 'Avställd'), ('Beslutad', 'Beslutad'), ('Definiera ej', 'Definiera ej'), ('För validering', 'För validering'), ('Internremiss', 'Internremiss'), ('Preliminär', 'Preliminär'), ('Publicera ej', 'Publicera ej'), ('Pågår', 'Pågår'), ('Ej Påbörjad', 'Ej Påbörjad')], default='Ej Påbörjad', max_length=255),
        ),
        migrations.AlterField(
            model_name='kommenterabegreppdefinition',
            name='status',
            field=models.CharField(choices=[('Avråds', 'Avråds'), ('Avställd', 'Avställd'), ('Beslutad', 'Beslutad'), ('Definiera ej', 'Definiera ej'), ('För validering', 'För validering'), ('Internremiss', 'Internremiss'), ('Preliminär', 'Preliminär'), ('Publicera ej', 'Publicera ej'), ('Pågår', 'Pågår'), ('Ej Påbörjad', 'Ej Påbörjad')], default='Ej Påbörjad', max_length=50),
        ),
        migrations.RenameModel(
            old_name='KommenteraBegreppDefinition',
            new_name='KommenteraBegrepp',
        ),
        migrations.AlterField(
            model_name='begreppexternalfiles',
            name='kommentar',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='ordbok.kommenterabegrepp'),
        ),
    ]