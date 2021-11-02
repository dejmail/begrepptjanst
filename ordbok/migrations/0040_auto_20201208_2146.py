# Generated by Django 3.0.3 on 2020-12-08 21:46

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ordbok', '0039_begrepp_validated_by'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='begrepp',
            name='validated_by',
        ),
        migrations.AlterField(
            model_name='doman',
            name='begrepp',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='begrepp_fk', to='ordbok.Begrepp'),
        ),
        migrations.AlterField(
            model_name='doman',
            name='domän_kontext',
            field=models.TextField(blank=True, null=True),
        )
    ]