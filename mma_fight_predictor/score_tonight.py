"""Morning scoring: compare last night's predictions to the real results.
First ingest the results, then score:
    python manage.py backfill_data --fights-only
    python manage.py shell -c "exec(open('score_tonight.py').read())"
"""
import json
import unicodedata

from django.db.models import Q

from mma_fight_predictor_api.Fighter.models import Fighter
from mma_fight_predictor_api.Fights.models import Fight

PATH = "predictions_ufc_2026-06-20.json"


def norm(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode("ascii").lower()
    return " ".join(s.split())


with open(PATH) as fh:
    data = json.load(fh)

lookup = {}
for f in Fighter.objects.all():
    lookup.setdefault(norm(f.get_full_name()), f)

scored = correct = 0
print(f"\n{'='*78}\nScoring: {data['event']}  (model: {data.get('model')})\n{'='*78}")
for r in data["predictions"]:
    if not r.get("resolved"):
        print(f"  {r['fighter_a']} vs {r['fighter_b']:24} -> not predicted")
        continue
    fa, fb = lookup.get(norm(r["fighter_a"])), lookup.get(norm(r["fighter_b"]))
    fight = None
    if fa and fb:
        fight = (
            Fight.objects.filter(
                Q(blue_fighter=fa, red_fighter=fb) | Q(blue_fighter=fb, red_fighter=fa)
            )
            .order_by("-date")
            .first()
        )
    if not fight or not fight.winner:
        r["actual_winner"] = None
        r["correct"] = None
        print(f"  {r['fighter_a']} vs {r['fighter_b']:24} -> result not in DB yet")
        continue
    r["actual_winner"] = fight.winner
    r["correct"] = norm(fight.winner) == norm(r["predicted_winner"])
    scored += 1
    correct += 1 if r["correct"] else 0
    mark = "✓" if r["correct"] else "✗"
    print(f"{mark} {r['fighter_a']} vs {r['fighter_b']:24} -> picked {r['predicted_winner']:18} "
          f"| actual {fight.winner}")

data["scored"] = scored
data["correct_count"] = correct
data["accuracy"] = round(correct / scored, 4) if scored else None
with open(PATH, "w") as fh:
    json.dump(data, fh, indent=2)

if scored:
    print(f"\nRESULT: {correct}/{scored} correct = {correct / scored * 100:.1f}% accuracy")
else:
    print("\nNo results found yet -- run `backfill_data --fights-only` once the card is over.")
