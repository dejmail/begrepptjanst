# Generated by Django 4.2.15 on 2024-08-20 12:36

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ordbok', '0050_remove_doman_users_doman_groups'),
    ]

    operations = [
        migrations.AlterField(
            model_name='begrepp',
            name='beställare',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='begrepp', to='ordbok.bestallare'),
        ),
    ]
