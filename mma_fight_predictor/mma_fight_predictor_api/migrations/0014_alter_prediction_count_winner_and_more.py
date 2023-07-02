# Generated by Django 4.2.1 on 2023-06-25 20:39

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("mma_fight_predictor_api", "0013_alter_prediction_fight_date"),
    ]

    operations = [
        migrations.AlterField(
            model_name="prediction",
            name="count_winner",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.DO_NOTHING,
                related_name="count_winner",
                to="mma_fight_predictor_api.fighter",
            ),
        ),
        migrations.AlterField(
            model_name="prediction",
            name="overall_winner",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.DO_NOTHING,
                related_name="overall_winner",
                to="mma_fight_predictor_api.fighter",
            ),
        ),
    ]