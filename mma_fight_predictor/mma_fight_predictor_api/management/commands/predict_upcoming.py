"""
Predict and save the next upcoming UFC card.

    python manage.py predict_upcoming

Auto-discovers the next event on ufcstats, predicts every fight whose fighters
are in the DB, and saves each as a ModelPrediction (idempotent -- safe to
re-run). Run this BEFORE the card so the predictions are genuine pre-fight
calls that score_predictions can grade afterwards.
"""
import unicodedata
from datetime import datetime

from django.core.management.base import BaseCommand

try:
    from mma_fight_predictor.mma_fight_predictor_api.Fighter.models import Fighter
    from mma_fight_predictor.mma_fight_predictor_api.ml.models import ModelPrediction
    from mma_fight_predictor.mma_fight_predictor_api.ml.predict import load_model, predict_matchup
    from mma_fight_predictor.mma_fight_predictor_api.ml.features import compute_current_accumulators
    from mma_fight_predictor.mma_fight_predictor_api.helpers.helpers import (
        get_upcoming_events, get_all_fights_in_event,
    )
except ModuleNotFoundError:  # pragma: no cover - dev app label
    from mma_fight_predictor_api.Fighter.models import Fighter
    from mma_fight_predictor_api.ml.models import ModelPrediction
    from mma_fight_predictor_api.ml.predict import load_model, predict_matchup
    from mma_fight_predictor_api.ml.features import compute_current_accumulators
    from mma_fight_predictor_api.helpers.helpers import (
        get_upcoming_events, get_all_fights_in_event,
    )


def norm(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode("ascii").lower()
    return " ".join(s.split())


class Command(BaseCommand):
    help = "Predict and save the next upcoming UFC card."

    def handle(self, *args, **options):
        events = list(get_upcoming_events())
        if not events:
            self.stdout.write(self.style.WARNING("No upcoming events found."))
            return
        event = events[0]
        fights = get_all_fights_in_event(event)
        self.stdout.write(f"Next event: {event['name']} ({len(fights)} fights)")

        event_date = None
        if fights:
            try:
                event_date = datetime.strptime(fights[0]["date"].strip(), "%B %d, %Y").date()
            except (ValueError, TypeError, KeyError):
                self.stdout.write(self.style.WARNING("Could not parse event date."))

        lookup = {}
        for f in Fighter.objects.all():
            lookup.setdefault(norm(f.get_full_name()), f)

        bundle = load_model()
        acc = compute_current_accumulators()

        saved = skipped = 0
        for fight in fights:
            a_name, b_name = fight["fighter_1"], fight["fighter_2"]
            fa, fb = lookup.get(norm(a_name)), lookup.get(norm(b_name))
            if not fa or not fb:
                missing = [n for n, f in ((a_name, fa), (b_name, fb)) if not f]
                self.stdout.write(f"  skip (not in DB): {', '.join(missing)}")
                skipped += 1
                continue

            result = predict_matchup(fa.get_full_name(), fb.get_full_name(), bundle=bundle, acc=acc)
            _, created = ModelPrediction.objects.get_or_create(
                fighter_a=fa, fighter_b=fb, event_date=event_date,
                defaults=dict(
                    fighter_a_name=a_name, fighter_b_name=b_name,
                    prob_a=result["prob_a"], favorite=result["favorite"],
                    model_name=result["model"], model_trained_at=result.get("model_trained_at"),
                ),
            )
            conf = max(result["prob_a"], result["prob_b"]) * 100
            if created:
                saved += 1
                self.stdout.write(f"  {a_name} vs {b_name} -> {result['favorite']} ({conf:.0f}%)")
            else:
                skipped += 1
                self.stdout.write(f"  exists: {a_name} vs {b_name}")

        self.stdout.write(self.style.SUCCESS(
            f"\nSaved {saved}, skipped {skipped} for '{event['name']}' (event_date={event_date})."
        ))
