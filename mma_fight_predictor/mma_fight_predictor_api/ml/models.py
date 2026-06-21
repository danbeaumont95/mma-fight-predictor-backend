"""Persistence for win-probability model predictions.

A prediction's value is point-in-time: the model's answer for the same matchup
changes once a result enters the data (career stats update). So we snapshot
each prediction when it is made, and fill in the actual result later. This is
what makes honest accuracy/calibration tracking over many cards possible.

Kept separate from the heuristic `Prediction` table on purpose -- additive,
decoupled.
"""
from django.db import models

from ..Fighter.models import Fighter
from ..Fights.models import Fight


class ModelPrediction(models.Model):
    # Who fought (FK for joins) + the name as supplied (display snapshot).
    fighter_a = models.ForeignKey(
        Fighter, on_delete=models.DO_NOTHING, related_name="model_prediction_fighter_a"
    )
    fighter_b = models.ForeignKey(
        Fighter, on_delete=models.DO_NOTHING, related_name="model_prediction_fighter_b"
    )
    fighter_a_name = models.CharField(max_length=120)
    fighter_b_name = models.CharField(max_length=120)

    # The prediction itself.
    prob_a = models.FloatField()              # P(fighter_a wins)
    favorite = models.CharField(max_length=120)
    model_name = models.CharField(max_length=60, blank=True, null=True)
    model_trained_at = models.CharField(max_length=40, blank=True, null=True)
    predicted_at = models.DateTimeField(auto_now_add=True)
    event_date = models.DateField(blank=True, null=True)

    # Filled in after the fight by `manage.py score_predictions`.
    fight = models.ForeignKey(
        Fight, on_delete=models.SET_NULL, blank=True, null=True,
        related_name="model_predictions",
    )
    actual_winner = models.CharField(max_length=120, blank=True, null=True)
    correct = models.BooleanField(blank=True, null=True)
    scored_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.fighter_a_name} vs {self.fighter_b_name} (p={self.prob_a:.2f})"
