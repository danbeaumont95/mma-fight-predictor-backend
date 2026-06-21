"""
Turn the trained win-probability model into actual matchup predictions.

`predict_matchup("Ilia Topuria", "Justin Gaethje")` resolves both fighters,
rebuilds their current point-in-time features, and returns each fighter's win
probability from the saved model.
"""
import os

import joblib
import numpy as np

from .features import compute_current_accumulators, matchup_difference_features
from ..helpers.helpers import find_fighter_by_full_name

MODEL_PATH = os.path.join(os.path.dirname(__file__), "models", "win_model.joblib")


def load_model():
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(
            f"No trained model at {MODEL_PATH}. Run: python manage.py train_win_model"
        )
    return joblib.load(MODEL_PATH)


def predict_matchup(name_a, name_b, bundle=None, acc=None, as_of=None):
    """Return win probabilities for a hypothetical bout between two fighters.

    `bundle` (loaded model) and `acc` (career accumulators) can be passed in to
    avoid recomputing them when scoring many matchups in a loop.
    """
    fa = find_fighter_by_full_name(name_a)
    fb = find_fighter_by_full_name(name_b)
    missing = [n for n, f in ((name_a, fa), (name_b, fb)) if f is None]
    if missing:
        raise ValueError(f"Fighter(s) not found: {missing}")
    if fa.id == fb.id:
        raise ValueError("Both names resolve to the same fighter.")

    bundle = bundle or load_model()
    acc = acc if acc is not None else compute_current_accumulators()
    model = bundle["model"]

    # Score both orderings and average so the result is exactly symmetric
    # (median-imputed missing values don't otherwise flip sign on swap).
    feats_ab = np.array([matchup_difference_features(fa, fb, acc, as_of=as_of)], dtype=float)
    feats_ba = np.array([matchup_difference_features(fb, fa, acc, as_of=as_of)], dtype=float)
    p_ab = float(model.predict_proba(feats_ab)[0, 1])      # P(A beats B)
    p_ba = float(model.predict_proba(feats_ba)[0, 1])      # P(B beats A)
    prob_a = (p_ab + (1.0 - p_ba)) / 2.0

    return {
        "fighter_a": fa.get_full_name(),
        "fighter_b": fb.get_full_name(),
        "prob_a": round(prob_a, 4),
        "prob_b": round(1.0 - prob_a, 4),
        "favorite": fa.get_full_name() if prob_a >= 0.5 else fb.get_full_name(),
        "model": bundle.get("model_name"),
    }
