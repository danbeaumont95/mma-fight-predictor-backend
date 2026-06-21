"""One-off: import genuine pre-fight predictions from a predict_tonight JSON
into the ModelPrediction table (so they can be scored in the new system).
Run:  python manage.py shell -c "exec(open('import_predictions.py').read())"
"""
import json
import unicodedata
from datetime import datetime

from django.utils.dateparse import parse_datetime

from mma_fight_predictor_api.Fighter.models import Fighter
from mma_fight_predictor_api.ml.models import ModelPrediction
from mma_fight_predictor_api.ml.predict import load_model

PATH = "predictions_ufc_2026-06-20.json"
EVENT_DATE = datetime.strptime("2026-06-20", "%Y-%m-%d").date()


def norm(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode("ascii").lower()
    return " ".join(s.split())


lookup = {}
for f in Fighter.objects.all():
    lookup.setdefault(norm(f.get_full_name()), f)

with open(PATH) as fh:
    data = json.load(fh)

trained_at = load_model().get("trained_at")
gen_at = parse_datetime(data.get("generated_at") or "")

created = skipped = 0
for r in data["predictions"]:
    if not r.get("resolved"):
        print(f"skip (unresolved): {r['fighter_a']} vs {r['fighter_b']}")
        skipped += 1
        continue
    fa, fb = lookup.get(norm(r["fighter_a"])), lookup.get(norm(r["fighter_b"]))
    if not fa or not fb:
        print(f"skip (not in DB): {r['fighter_a']} vs {r['fighter_b']}")
        skipped += 1
        continue

    obj, was_created = ModelPrediction.objects.get_or_create(
        fighter_a=fa, fighter_b=fb, event_date=EVENT_DATE,
        defaults=dict(
            fighter_a_name=r["fighter_a"], fighter_b_name=r["fighter_b"],
            prob_a=r["prob_a"], favorite=r["predicted_winner"],
            model_name=data.get("model"), model_trained_at=trained_at,
        ),
    )
    if was_created:
        if gen_at:
            # auto_now_add set predicted_at to now; restore the genuine time.
            ModelPrediction.objects.filter(id=obj.id).update(predicted_at=gen_at)
        created += 1
        print(f"imported: {r['fighter_a']} vs {r['fighter_b']} -> "
              f"{r['predicted_winner']} ({r['prob_favorite'] * 100:.0f}%)")
    else:
        skipped += 1
        print(f"exists, skipped: {r['fighter_a']} vs {r['fighter_b']}")

print(f"\nImported {created}, skipped {skipped}. "
      f"Total ModelPredictions: {ModelPrediction.objects.count()}")
print("Next: python manage.py score_predictions")
