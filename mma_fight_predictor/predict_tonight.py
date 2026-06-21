"""One-off: predict tonight's card and save to a dated JSON file.
Run:  python manage.py shell -c "exec(open('predict_tonight.py').read())"
"""
import json
import unicodedata
import datetime
import numpy as np

from mma_fight_predictor_api.Fighter.models import Fighter
from mma_fight_predictor_api.ml.predict import load_model
from mma_fight_predictor_api.ml.features import (
    compute_current_accumulators,
    matchup_difference_features,
)


def norm(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii").lower()
    return " ".join(s.split())


# accent/space-insensitive lookup of every fighter
lookup = {}
for f in Fighter.objects.all():
    lookup.setdefault(norm(f.get_full_name()), f)

bundle = load_model()
model = bundle["model"]
acc = compute_current_accumulators()


def prob_a(fa, fb):
    ab = np.array([matchup_difference_features(fa, fb, acc)], dtype=float)
    ba = np.array([matchup_difference_features(fb, fa, acc)], dtype=float)
    return float((model.predict_proba(ab)[0, 1] + (1 - model.predict_proba(ba)[0, 1])) / 2)


# (weight_class, fighter_a, record_a, fighter_b, record_b, is_main_event)
card = [
    ("Flyweight", "André Lima", "11-0-0", "Kevin Borjas", "10-5-0", False),
    ("Women Bantamweight", "Beatriz Mesquita", "7-0-0", "Melissa Mullins", "7-2-0", False),
    ("Flyweight", "Allan Nascimento", "22-6-0", "Mitch Raposo", "10-3-0", False),
    ("Featherweight", "Gaston Bolanos", "8-5-0", "Michael Aswell Jr.", "11-4-0", False),
    ("Women Bantamweight", "Karol Rosa", "19-7-0", "Luana Santos", "10-2-0", False),
    ("Flyweight", "Manel Kape", "22-7-0", "Kyoji Horiguchi", "36-5-0", True),
    ("Light Heavyweight", "Ion Cutelaba", "20-11-1", "Navajo Stirling", "9-0-0", False),
    ("Featherweight", "Hyder Amil", "11-2-0", "Christian Rodriguez", "12-4-0", False),
    ("Featherweight", "Melsik Baghdasaryan", "8-3-0", "Murtazali Magomedov", "10-0-0", False),
]

preds = []
for wc, an, ar, bn, br, main in card:
    fa, fb = lookup.get(norm(an)), lookup.get(norm(bn))
    rec = {"weight_class": wc, "main_event": main,
           "fighter_a": an, "record_a": ar, "fighter_b": bn, "record_b": br}
    if not fa or not fb:
        rec.update({"resolved": False,
                    "unmatched": [n for n, f in ((an, fa), (bn, fb)) if not f],
                    "predicted_winner": None, "prob_favorite": None,
                    "actual_winner": None, "correct": None})
    else:
        p = prob_a(fa, fb)
        rec.update({"resolved": True,
                    "predicted_winner": an if p >= 0.5 else bn,
                    "prob_favorite": round(max(p, 1 - p), 4),
                    "prob_a": round(p, 4),
                    "actual_winner": None, "correct": None})
    preds.append(rec)

out = {"generated_at": datetime.datetime.now().isoformat(),
       "event": "UFC Fight Night (2026-06-20/21)",
       "model": bundle.get("model_name"),
       "note": "Fill in 'actual_winner' tomorrow; 'correct' compares to 'predicted_winner'.",
       "predictions": preds}

path = "predictions_ufc_2026-06-20.json"
with open(path, "w") as fh:
    json.dump(out, fh, indent=2)

print(f"\n{'='*72}\nUFC Fight Night predictions  (model: {bundle.get('model_name')})\n{'='*72}")
for r in preds:
    star = "★" if r["main_event"] else " "
    matchup = f"{r['fighter_a']} vs {r['fighter_b']}"
    if r["resolved"]:
        print(f"{star} {matchup:42} -> {r['predicted_winner']:20} {r['prob_favorite']*100:4.0f}%")
    else:
        print(f"{star} {matchup:42} -> SKIPPED (not in DB: {', '.join(r['unmatched'])})")
n_pred = sum(1 for r in preds if r["resolved"])
print(f"\nSaved {n_pred}/{len(preds)} predictions -> {path}")
