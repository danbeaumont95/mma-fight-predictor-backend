"""
Predict the winner of a hypothetical matchup using the trained model.

    python manage.py predict_fight "Ilia Topuria" "Justin Gaethje"
"""
from django.core.management.base import BaseCommand, CommandError

try:
    from mma_fight_predictor.mma_fight_predictor_api.ml.predict import predict_matchup
except ModuleNotFoundError:  # pragma: no cover - dev app label
    from mma_fight_predictor_api.ml.predict import predict_matchup


class Command(BaseCommand):
    help = "Predict win probabilities for a matchup between two fighters."

    def add_arguments(self, parser):
        parser.add_argument("fighter_a")
        parser.add_argument("fighter_b")

    def handle(self, *args, **options):
        try:
            result = predict_matchup(options["fighter_a"], options["fighter_b"])
        except (ValueError, FileNotFoundError) as e:
            raise CommandError(str(e))

        a, b = result["fighter_a"], result["fighter_b"]
        self.stdout.write("")
        self.stdout.write(f"  {a:28} {result['prob_a'] * 100:5.1f}%")
        self.stdout.write(f"  {b:28} {result['prob_b'] * 100:5.1f}%")
        self.stdout.write(
            self.style.SUCCESS(
                f"\n  Pick: {result['favorite']}  (model: {result['model']})"
            )
        )
