# Generated by Django 3.0.3 on 2020-10-08 13:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ordbok', '0032_auto_20201008_1243'),
    ]

    operations = [
        migrations.AlterField(
            model_name='begreppexternalfiles',
            name='support_file',
            field=models.FileField(blank=True, null=True, upload_to=''),
        ),
    ]
