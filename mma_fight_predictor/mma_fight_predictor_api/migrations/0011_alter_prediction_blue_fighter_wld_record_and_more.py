# Generated by Django 4.2.1 on 2023-06-25 15:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("mma_fight_predictor_api", "0010_prediction"),
    ]

    operations = [
        migrations.AlterField(
            model_name="prediction",
            name="blue_fighter_wld_record",
            field=models.CharField(max_length=20),
        ),
        migrations.AlterField(
            model_name="prediction",
            name="red_fighter_wld_record",
            field=models.CharField(max_length=20),
        ),
    ]