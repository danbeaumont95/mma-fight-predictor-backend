"""
Repopulate the database with up-to-date fighters and fights scraped from
ufcstats.com.

Usage:
    python manage.py backfill_data                 # fighters, then fights (full)
    python manage.py backfill_data --fighters-only
    python manage.py backfill_data --fights-only
    python manage.py backfill_data --skip-recent 2 # mimic the old endpoint

This wraps the existing scrapers in helpers/scraping.py. Unlike the
`/fighter/scrape_fight_stats` endpoint (which skips the 2 newest events),
this command scrapes ALL completed events by default (--skip-recent 0) so a
stale database can be brought fully up to date.

Scope: raw Fighter + Fight tables only. Predictions/odds are derived data and
are intentionally NOT touched here.
"""
from django.core.management.base import BaseCommand

# The app is installed under different labels depending on how Django is
# invoked (see settings.py / apps.py), so import defensively.
try:
    from mma_fight_predictor.mma_fight_predictor_api.helpers.scraping import (
        scrape_raw_fighter_details,
        scrape_raw_fight_details,
    )
    from mma_fight_predictor.mma_fight_predictor_api.Fighter.models import Fighter
    from mma_fight_predictor.mma_fight_predictor_api.Fights.models import Fight
except ModuleNotFoundError:  # pragma: no cover - fallback for the dev app label
    from mma_fight_predictor_api.helpers.scraping import (
        scrape_raw_fighter_details,
        scrape_raw_fight_details,
    )
    from mma_fight_predictor_api.Fighter.models import Fighter
    from mma_fight_predictor_api.Fights.models import Fight


class Command(BaseCommand):
    help = "Scrape ufcstats.com to repopulate the Fighter and Fight tables."

    def add_arguments(self, parser):
        parser.add_argument(
            "--fighters-only",
            action="store_true",
            help="Only scrape fighters (skip fights).",
        )
        parser.add_argument(
            "--fights-only",
            action="store_true",
            help="Only scrape fights (skip fighters). Fighters must already exist.",
        )
        parser.add_argument(
            "--skip-recent",
            type=int,
            default=0,
            help=(
                "Number of newest completed events to skip when scraping fights. "
                "Defaults to 0 (scrape everything). Use 2 to mimic the old endpoint."
            ),
        )
        parser.add_argument(
            "--update-existing",
            action="store_true",
            help=(
                "Refresh stats (record, reach, SLpM, etc.) for fighters already in "
                "the DB, not just newly-created ones. Fetches every fighter's profile "
                "page, so it is much slower."
            ),
        )

    def handle(self, *args, **options):
        fighters_only = options["fighters_only"]
        fights_only = options["fights_only"]
        skip_recent = options["skip_recent"]
        update_existing = options["update_existing"]

        if fighters_only and fights_only:
            self.stderr.write(
                self.style.ERROR("Pass at most one of --fighters-only / --fights-only.")
            )
            return

        do_fighters = not fights_only
        do_fights = not fighters_only

        if do_fighters:
            before = Fighter.objects.count()
            mode = (
                "refreshing existing + adding new"
                if update_existing
                else "adding new only"
            )
            self.stdout.write(
                self.style.WARNING(
                    f"Scraping fighters (A-Z, {mode})... starting from {before} in DB. "
                    "Makes ~26 page requests plus one profile request per "
                    f"{'fighter' if update_existing else 'new fighter'} and is slow."
                )
            )
            scrape_raw_fighter_details(update_existing=update_existing)
            after = Fighter.objects.count()
            self.stdout.write(
                self.style.SUCCESS(
                    f"Fighters done: {after} total (+{after - before} new)."
                )
            )

        if do_fights:
            before = Fight.objects.count()
            self.stdout.write(
                self.style.WARNING(
                    f"Scraping fights (skip_recent={skip_recent})... starting from "
                    f"{before} in DB. Errors are also written to errors-4.txt."
                )
            )
            scrape_raw_fight_details(skip_recent=skip_recent)
            after = Fight.objects.count()
            self.stdout.write(
                self.style.SUCCESS(
                    f"Fights done: {after} total (+{after - before} new)."
                )
            )

        self.stdout.write(self.style.SUCCESS("Backfill complete."))
