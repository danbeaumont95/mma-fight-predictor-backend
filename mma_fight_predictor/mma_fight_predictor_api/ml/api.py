"""
HTTP endpoint for the win-probability model.

    POST /mma_fight_predictor/predict_fight
    body: {"fighter_a": "Manel Kape", "fighter_b": "Kyoji Horiguchi"}
    ->    {"fighter_a": ..., "fighter_b": ..., "prob_a": 0.52, "prob_b": 0.48,
           "favorite": ..., "model": "logistic_regression"}

The trained model and each fighter's career accumulators are expensive to
build, so they are cached at the process level and only rebuilt when the data
(fight count) or the model file changes -- no per-request recomputation.
"""
import os

from rest_framework import status
from rest_framework.decorators import api_view

from datetime import datetime

from ..Fighter.models import Fighter
from ..Fights.models import Fight
from ..helpers.helpers import return_response
from .features import compute_current_accumulators
from .models import ModelPrediction
from .predict import MODEL_PATH, load_model, predict_matchup

_CACHE = {"bundle": None, "mtime": None, "acc": None, "n_fights": None}


def get_context():
    """Return (model_bundle, career_accumulators), cached across requests."""
    n_fights = Fight.objects.count()
    if _CACHE["acc"] is None or _CACHE["n_fights"] != n_fights:
        _CACHE["acc"] = compute_current_accumulators()
        _CACHE["n_fights"] = n_fights

    mtime = os.path.getmtime(MODEL_PATH) if os.path.exists(MODEL_PATH) else None
    if _CACHE["bundle"] is None or _CACHE["mtime"] != mtime:
        _CACHE["bundle"] = load_model()
        _CACHE["mtime"] = mtime

    return _CACHE["bundle"], _CACHE["acc"]


@api_view(["POST"])
def predict_fight(request):
    fighter_a = (request.data.get("fighter_a") or "").strip()
    fighter_b = (request.data.get("fighter_b") or "").strip()
    if not fighter_a or not fighter_b:
        return return_response(
            {}, "Provide both 'fighter_a' and 'fighter_b'.", status.HTTP_400_BAD_REQUEST
        )

    try:
        bundle, acc = get_context()
        result = predict_matchup(fighter_a, fighter_b, bundle=bundle, acc=acc)
    except FileNotFoundError as e:
        # Model not trained yet.
        return return_response({}, str(e), status.HTTP_503_SERVICE_UNAVAILABLE)
    except ValueError as e:
        # Unknown fighter, or both names resolve to the same fighter.
        return return_response({}, str(e), status.HTTP_400_BAD_REQUEST)

    # Opt-in persistence: pass {"save": true} to log this prediction for later
    # accuracy/calibration scoring (don't pollute the table on casual lookups).
    if request.data.get("save"):
        event_date = request.data.get("event_date")
        prediction = ModelPrediction.objects.create(
            fighter_a=Fighter.objects.get(id=result["fighter_a_id"]),
            fighter_b=Fighter.objects.get(id=result["fighter_b_id"]),
            fighter_a_name=result["fighter_a"],
            fighter_b_name=result["fighter_b"],
            prob_a=result["prob_a"],
            favorite=result["favorite"],
            model_name=result["model"],
            model_trained_at=result.get("model_trained_at"),
            event_date=datetime.strptime(event_date, "%Y-%m-%d").date() if event_date else None,
        )
        result["prediction_id"] = prediction.id

    return return_response(result, "Success", status.HTTP_200_OK)
