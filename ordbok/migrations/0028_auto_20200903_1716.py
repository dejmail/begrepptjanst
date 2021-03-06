# Generated by Django 3.0.3 on 2020-09-03 17:16

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ordbok', '0027_bestallare_önskad_slutdatum'),
    ]

    operations = [
        migrations.CreateModel(
            name='BegreppExternalFiles',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('support_file', models.FileField(blank=True, null=True, upload_to='uploads')),
                ('begrepp', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='ordbok.Begrepp')),
            ],
        ),
    ]
