# Generated by Django 3.0.3 on 2020-10-08 13:23

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ordbok', '0033_auto_20201008_1303'),
    ]

    operations = [
        migrations.AlterField(
            model_name='opponerabegreppdefinition',
            name='begrepp',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='ordbok.Begrepp'),
        ),
    ]
