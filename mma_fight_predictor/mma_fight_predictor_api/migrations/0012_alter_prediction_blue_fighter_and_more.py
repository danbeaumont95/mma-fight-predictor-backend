# Generated by Django 4.2.1 on 2023-06-25 20:28

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        (
            "mma_fight_predictor_api",
            "0011_alter_prediction_blue_fighter_wld_record_and_more",
        ),
    ]

    operations = [
        migrations.AlterField(
            model_name="prediction",
            name="blue_fighter",
            field=models.ForeignKey(
                default=None,
                on_delete=django.db.models.deletion.DO_NOTHING,
                related_name="prediction_blue_fighter",
                to="mma_fight_predictor_api.fighter",
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="prediction",
            name="count_winner",
            field=models.ForeignKey(
                default=None,
                on_delete=django.db.models.deletion.DO_NOTHING,
                related_name="count_winner",
                to="mma_fight_predictor_api.fighter",
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="prediction",
            name="defense_winner",
            field=models.ForeignKey(
                default=None,
                on_delete=django.db.models.deletion.DO_NOTHING,
                related_name="defense_winner",
                to="mma_fight_predictor_api.fighter",
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="prediction",
            name="fight_date",
            field=models.DateField(blank=True, default=None),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="prediction",
            name="fight_winner",
            field=models.ForeignKey(
                default=None,
                on_delete=django.db.models.deletion.DO_NOTHING,
                related_name="fight_winner",
                to="mma_fight_predictor_api.fighter",
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="prediction",
            name="overall_winner",
            field=models.ForeignKey(
                default=None,
                on_delete=django.db.models.deletion.DO_NOTHING,
                related_name="overall_winner",
                to="mma_fight_predictor_api.fighter",
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="prediction",
            name="reach_winner",
            field=models.ForeignKey(
                default=None,
                on_delete=django.db.models.deletion.DO_NOTHING,
                related_name="reach_winner",
                to="mma_fight_predictor_api.fighter",
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="prediction",
            name="red_fighter",
            field=models.ForeignKey(
                default=None,
                on_delete=django.db.models.deletion.DO_NOTHING,
                related_name="prediction_red_fighter",
                to="mma_fight_predictor_api.fighter",
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="prediction",
            name="sapm_winner",
            field=models.ForeignKey(
                default=None,
                on_delete=django.db.models.deletion.DO_NOTHING,
                related_name="sapm_winner",
                to="mma_fight_predictor_api.fighter",
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="prediction",
            name="slpm_winner",
            field=models.ForeignKey(
                default=None,
                on_delete=django.db.models.deletion.DO_NOTHING,
                related_name="slpm_winner",
                to="mma_fight_predictor_api.fighter",
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="prediction",
            name="striking_accuracy_winner",
            field=models.ForeignKey(
                default=None,
                on_delete=django.db.models.deletion.DO_NOTHING,
                related_name="striking_accuracy_winner",
                to="mma_fight_predictor_api.fighter",
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="prediction",
            name="submission_average_15_min_average_winner",
            field=models.ForeignKey(
                default=None,
                on_delete=django.db.models.deletion.DO_NOTHING,
                related_name="submission_average_15_min_average_winner",
                to="mma_fight_predictor_api.fighter",
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="prediction",
            name="takedown_accuracy_winner",
            field=models.ForeignKey(
                default=None,
                on_delete=django.db.models.deletion.DO_NOTHING,
                related_name="takedown_accuracy_winner",
                to="mma_fight_predictor_api.fighter",
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="prediction",
            name="takedown_average_15_min_winner",
            field=models.ForeignKey(
                default=None,
                on_delete=django.db.models.deletion.DO_NOTHING,
                related_name="takedown_average_15_min_winner",
                to="mma_fight_predictor_api.fighter",
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="prediction",
            name="takedown_average_winner",
            field=models.ForeignKey(
                default=None,
                on_delete=django.db.models.deletion.DO_NOTHING,
                related_name="takedown_average_winner",
                to="mma_fight_predictor_api.fighter",
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="prediction",
            name="takedown_defense_winner",
            field=models.ForeignKey(
                default=None,
                on_delete=django.db.models.deletion.DO_NOTHING,
                related_name="takedown_defense_winner",
                to="mma_fight_predictor_api.fighter",
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="prediction",
            name="wld_winner",
            field=models.ForeignKey(
                default=None,
                on_delete=django.db.models.deletion.DO_NOTHING,
                related_name="wld_winner",
                to="mma_fight_predictor_api.fighter",
            ),
            preserve_default=False,
        ),
    ]
