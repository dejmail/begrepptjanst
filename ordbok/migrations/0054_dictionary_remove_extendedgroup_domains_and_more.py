# Generated by Django 4.2.15 on 2024-08-21 14:09

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ordbok', '0053_extendedgroup_delete_group'),
    ]

    operations = [
        migrations.CreateModel(
            name='Dictionary',
            fields=[
                ('dictionary_id', models.AutoField(primary_key=True, serialize=False)),
                ('dictionary_context', models.TextField(blank=True, null=True)),
                ('dictionary_name', models.CharField(max_length=255)),
                ('begrepp', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='begrepp_fk', to='ordbok.begrepp')),
            ],
            options={
                'verbose_name_plural': 'Ordböcker',
            },
        ),
        migrations.RemoveField(
            model_name='extendedgroup',
            name='domains',
        ),
        migrations.RemoveField(
            model_name='extendedgroup',
            name='group',
        ),
        migrations.DeleteModel(
            name='Doman',
        ),
        migrations.DeleteModel(
            name='ExtendedGroup',
        ),
    ]
