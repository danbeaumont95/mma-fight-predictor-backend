# Generated by Django 4.2.1 on 2023-07-29 17:55

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("mma_fight_predictor_api", "0018_fight_weight"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="fight",
            name="weight",
        ),
    ]
