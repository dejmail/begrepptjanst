# Generated by Django 2.2.5 on 2020-11-05 08:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ordbok', '0038_auto_20201029_1303'),
    ]

    operations = [
        migrations.AddField(
            model_name='begrepp',
            name='validated_by',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
