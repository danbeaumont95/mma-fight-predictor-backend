# Generated by Django 4.2.1 on 2023-05-28 20:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("mma_fight_predictor_api", "0008_fight_format"),
    ]

    operations = [
        migrations.AddField(
            model_name="fight",
            name="loser",
            field=models.CharField(blank=True, max_length=40, null=True),
        ),
    ]
