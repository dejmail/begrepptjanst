# Generated by Django 2.2.5 on 2020-09-17 14:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ordbok', '0029_auto_20200904_1438'),
    ]

    operations = [
        migrations.AddField(
            model_name='begrepp',
            name='term_i_system',
            field=models.CharField(choices=[('Millenium', 'Millenium'), ('Annat system', 'Annat system'), ('VGR Begreppsystem', 'VGR Begreppsystem')], max_length=255, null=True, verbose_name='Används i system'),
        ),
    ]
