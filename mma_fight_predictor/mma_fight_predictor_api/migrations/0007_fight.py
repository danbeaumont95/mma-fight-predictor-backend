# Generated by Django 4.2.1 on 2023-05-15 19:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("mma_fight_predictor_api", "0006_alter_fighter_last_name"),
    ]

    operations = [
        migrations.CreateModel(
            name="Fight",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("r_kd", models.IntegerField(blank=True, null=True)),
                ("b_kd", models.IntegerField(blank=True, null=True)),
                ("r_sig_str", models.CharField(blank=True, max_length=20, null=True)),
                ("b_sig_str", models.CharField(blank=True, max_length=20, null=True)),
                (
                    "r_sig_str_pct",
                    models.CharField(blank=True, max_length=20, null=True),
                ),
                (
                    "b_sig_str_pct",
                    models.CharField(blank=True, max_length=20, null=True),
                ),
                ("r_total_str", models.CharField(blank=True, max_length=20, null=True)),
                ("b_total_str", models.CharField(blank=True, max_length=20, null=True)),
                ("r_td", models.CharField(blank=True, max_length=20, null=True)),
                ("b_td", models.CharField(blank=True, max_length=20, null=True)),
                ("r_td_pct", models.CharField(blank=True, max_length=20, null=True)),
                ("b_td_pct", models.CharField(blank=True, max_length=20, null=True)),
                ("r_sub_att", models.CharField(blank=True, max_length=20, null=True)),
                ("b_sub_att", models.CharField(blank=True, max_length=20, null=True)),
                ("r_rev", models.CharField(blank=True, max_length=20, null=True)),
                ("b_rev", models.CharField(blank=True, max_length=20, null=True)),
                ("r_ctrl", models.CharField(blank=True, max_length=20, null=True)),
                ("b_ctrl", models.CharField(blank=True, max_length=20, null=True)),
                ("r_head", models.CharField(blank=True, max_length=20, null=True)),
                ("b_head", models.CharField(blank=True, max_length=20, null=True)),
                ("r_body", models.CharField(blank=True, max_length=20, null=True)),
                ("b_body", models.CharField(blank=True, max_length=20, null=True)),
                ("r_leg", models.CharField(blank=True, max_length=20, null=True)),
                ("b_leg", models.CharField(blank=True, max_length=20, null=True)),
                ("r_distance", models.CharField(blank=True, max_length=20, null=True)),
                ("b_distance", models.CharField(blank=True, max_length=20, null=True)),
                ("r_clinch", models.CharField(blank=True, max_length=20, null=True)),
                ("b_clinch", models.CharField(blank=True, max_length=20, null=True)),
                ("r_ground", models.CharField(blank=True, max_length=20, null=True)),
                ("b_ground", models.CharField(blank=True, max_length=20, null=True)),
                ("win_by", models.CharField(blank=True, max_length=20, null=True)),
                ("last_round", models.IntegerField(blank=True, null=True)),
                (
                    "last_round_time",
                    models.CharField(blank=True, max_length=20, null=True),
                ),
                ("referee", models.CharField(blank=True, max_length=40, null=True)),
                ("date", models.DateField(blank=True, null=True)),
                ("location", models.CharField(blank=True, max_length=40, null=True)),
                ("fight_type", models.CharField(blank=True, max_length=30, null=True)),
                ("winner", models.CharField(blank=True, max_length=40, null=True)),
                (
                    "blue_fighter",
                    models.ManyToManyField(
                        related_name="blue_fighter",
                        to="mma_fight_predictor_api.fighter",
                    ),
                ),
                (
                    "red_fighter",
                    models.ManyToManyField(
                        related_name="red_fighter", to="mma_fight_predictor_api.fighter"
                    ),
                ),
            ],
        ),
    ]
