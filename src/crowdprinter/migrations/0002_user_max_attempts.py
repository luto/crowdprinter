# Generated by Django 5.1.2 on 2024-12-09 17:59

from django.db import migrations
from django.db import models


class Migration(migrations.Migration):

    dependencies = [
        ("crowdprinter", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="max_attempts",
            field=models.IntegerField(
                blank=True,
                help_text="Maximale anzahl gleichzeitiger Drucke. 0 für unbegrenzt, leer = Default(3)",
                null=True,
            ),
        ),
    ]
