# Generated by Django 2.2.5 on 2020-02-21 11:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ordbok', '0002_opponerabegreppdefinition'),
    ]

    operations = [
        migrations.AlterField(
            model_name='doman',
            name='domän_id',
            field=models.AutoField(primary_key=True, serialize=False),
        ),
    ]
