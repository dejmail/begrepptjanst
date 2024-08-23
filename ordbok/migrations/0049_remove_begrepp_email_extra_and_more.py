# Generated by Django 4.2.15 on 2024-08-16 11:29

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('ordbok', '0048_auto_20220824_1139'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='begrepp',
            name='email_extra',
        ),
        migrations.RemoveField(
            model_name='historicalbegrepp',
            name='email_extra',
        ),
        migrations.AddField(
            model_name='doman',
            name='users',
            field=models.ManyToManyField(related_name='domains', to=settings.AUTH_USER_MODEL),
        ),
    ]
