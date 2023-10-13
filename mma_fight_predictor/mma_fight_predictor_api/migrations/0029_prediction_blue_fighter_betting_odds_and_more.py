# Generated by Django 4.2.1 on 2023-10-02 20:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        (
            "mma_fight_predictor_api",
            "0028_alter_token_access_token_alter_token_refresh_token",
        ),
    ]

    operations = [
        migrations.AddField(
            model_name="prediction",
            name="blue_fighter_betting_odds",
            field=models.CharField(default=None, max_length=20, null=True),
        ),
        migrations.AddField(
            model_name="prediction",
            name="red_fighter_betting_odds",
            field=models.CharField(default=None, max_length=20, null=True),
        ),
        migrations.DeleteModel(
            name="User",
        ),
    ]