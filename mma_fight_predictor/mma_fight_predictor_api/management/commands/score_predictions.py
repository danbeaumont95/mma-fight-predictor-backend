"""
Score saved model predictions against actual results.

    python manage.py backfill_data --fights-only --recent 2   # get results first
    python manage.py score_predictions                        # then score
    python manage.py score_predictions --all                  # re-score everything

For each unscored ModelPrediction it finds the real fight between the two
fighters (on/after the prediction date), records the actual winner and whether
the pick was correct, then prints overall accuracy and a calibration table
(does "70%" really win ~70% of the time?).
"""
import unicodedata

from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone

try:
    from mma_fight_predictor.mma_fight_predictor_api.ml.models import ModelPrediction
    from mma_fight_predictor.mma_fight_predictor_api.Fights.models import Fight
except ModuleNotFoundError:  # pragma: no cover - dev app label
    from mma_fight_predictor_api.ml.models import ModelPrediction
    from mma_fight_predictor_api.Fights.models import Fight


def norm(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode("ascii").lower()
    return " ".join(s.split())


class Command(BaseCommand):
    help = "Score saved model predictions against actual fight results."

    def add_arguments(self, parser):
        parser.add_argument("--all", action="store_true",
                            help="Re-score every prediction, not just unscored ones.")

    def handle(self, *args, **options):
        qs = ModelPrediction.objects.all()
        if not options["all"]:
            qs = qs.filter(correct__isnull=True)

        newly = 0
        for pred in qs:
            floor = pred.event_date or pred.predicted_at.date()
            fight = (
                Fight.objects.filter(
                    Q(blue_fighter=pred.fighter_a, red_fighter=pred.fighter_b)
                    | Q(blue_fighter=pred.fighter_b, red_fighter=pred.fighter_a),
                    date__gte=floor,
                )
                .exclude(winner__isnull=True)
                .exclude(winner__exact="")
                .order_by("date")
                .first()
            )
            if not fight:
                continue  # result not in the DB yet
            pred.fight = fight
            pred.actual_winner = fight.winner
            pred.correct = norm(fight.winner) == norm(pred.favorite)
            pred.scored_at = timezone.now()
            pred.save()
            newly += 1

        self._report(newly)

    def _report(self, newly):
        scored = ModelPrediction.objects.filter(correct__isnull=False)
        total = scored.count()
        self.stdout.write(self.style.SUCCESS(f"\nScored {newly} new prediction(s)."))
        if not total:
            self.stdout.write("No scored predictions yet.")
            return

        correct = scored.filter(correct=True).count()
        self.stdout.write(f"Overall: {correct}/{total} = {correct / total * 100:.1f}% accuracy\n")

        # Calibration: bucket by model confidence (max prob), compare predicted
        # confidence to the realised win rate.
        buckets = [(0.5, 0.6), (0.6, 0.7), (0.7, 0.8), (0.8, 1.01)]
        self.stdout.write(f"{'confidence':>12} {'n':>4} {'predicted':>10} {'actual':>8}")
        for lo, hi in buckets:
            rows = [p for p in scored if lo <= max(p.prob_a, 1 - p.prob_a) < hi]
            if not rows:
                continue
            pred_conf = sum(max(p.prob_a, 1 - p.prob_a) for p in rows) / len(rows)
            hit_rate = sum(1 for p in rows if p.correct) / len(rows)
            self.stdout.write(
                f"{f'{lo:.0%}-{hi if hi <= 1 else 1:.0%}':>12} {len(rows):>4} "
                f"{pred_conf * 100:9.1f}% {hit_rate * 100:7.1f}%"
            )
