# Generated by Django 4.2.1 on 2023-05-11 21:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("mma_fight_predictor_api", "0003_alter_fighter_gender"),
    ]

    operations = [
        migrations.AlterField(
            model_name="fighter",
            name="dob",
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AlterField(
            model_name="fighter",
            name="height",
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AlterField(
            model_name="fighter",
            name="reach",
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AlterField(
            model_name="fighter",
            name="stance",
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AlterField(
            model_name="fighter",
            name="weight",
            field=models.CharField(blank=True, max_length=20),
        ),
    ]
