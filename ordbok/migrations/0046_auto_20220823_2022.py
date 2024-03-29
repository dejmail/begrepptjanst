# Generated by Django 3.2.13 on 2022-08-23 20:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ordbok', '0045_auto_20220505_1324'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='begreppexternalfiles',
            options={'verbose_name_plural': 'Uppladdade filer'},
        ),
        # migrations.RemoveField(
        #     model_name='begrepp',
        #     name='email_extra',
        # ),
        # migrations.RemoveField(
        #     model_name='historicalbegrepp',
        #     name='email_extra',
        # ),
        migrations.AddField(
            model_name='begrepp',
            name='link',
            field=models.URLField(blank=True, help_text='Länk till dokument', null=True, verbose_name='länk'),
        ),
        migrations.AddField(
            model_name='historicalbegrepp',
            name='link',
            field=models.URLField(blank=True, help_text='Länk till dokument', null=True, verbose_name='länk'),
        ),
    ]
