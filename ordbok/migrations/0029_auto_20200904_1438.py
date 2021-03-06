# Generated by Django 3.0.3 on 2020-09-04 14:38

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ordbok', '0028_auto_20200903_1716'),
    ]

    operations = [
        migrations.AlterField(
            model_name='begreppexternalfiles',
            name='begrepp',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='ordbok.Begrepp'),
        ),
        migrations.AlterField(
            model_name='doman',
            name='begrepp',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='ordbok.Begrepp'),
        ),
        migrations.AlterField(
            model_name='synonym',
            name='begrepp',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='ordbok.Begrepp'),
        ),
    ]
