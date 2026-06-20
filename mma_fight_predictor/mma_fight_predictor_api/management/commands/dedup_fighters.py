"""
Find and merge duplicate Fighter records.

Two classes of duplicate exist:

1. EXACT duplicates - two rows whose full name ("first last") is identical.
   These are unambiguous and merged automatically.

2. FUZZY candidates - same last name where one first name is a prefix of the
   other or they share a first token (e.g. "chris duncan" vs
   "christian leroy duncan"). These are NOT merged automatically because they
   risk false positives; they are listed for you to merge by hand.

Usage:
    python manage.py dedup_fighters --dry-run     # preview exact-dup merges
    python manage.py dedup_fighters               # merge exact duplicates
    python manage.py dedup_fighters --candidates  # list fuzzy pairs to review
    python manage.py dedup_fighters --merge 959 958   # keep 959, fold 958 in

Merging repoints every foreign key (fights, etc.) from the removed fighter to
the kept one, then deletes the removed row.
"""
from collections import defaultdict

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Count, Q

try:
    from mma_fight_predictor.mma_fight_predictor_api.Fighter.models import Fighter
    from mma_fight_predictor.mma_fight_predictor_api.Fights.models import Fight
    from mma_fight_predictor.mma_fight_predictor_api.helpers.helpers import (
        normalized_full_name_expr,
    )
except ModuleNotFoundError:  # pragma: no cover - dev app label
    from mma_fight_predictor_api.Fighter.models import Fighter
    from mma_fight_predictor_api.Fights.models import Fight
    from mma_fight_predictor_api.helpers.helpers import normalized_full_name_expr


def fight_count(fighter):
    return Fight.objects.filter(
        Q(blue_fighter=fighter) | Q(red_fighter=fighter)
    ).count()


def _fill_missing_scalar_fields(keep, remove):
    """Copy non-empty values from `remove` into any empty field on `keep` so a
    merge never discards stats the kept row happens to be missing. Existing
    values on `keep` are never overwritten."""
    empty = (None, "", 0, 0.0)
    changed = False
    for field in keep._meta.fields:
        if field.primary_key:
            continue
        name = field.name
        if getattr(keep, name) in empty and getattr(remove, name) not in empty:
            setattr(keep, name, getattr(remove, name))
            changed = True
    if changed:
        keep.save()


def merge_fighters(keep, remove):
    """Repoint every FK from `remove` onto `keep`, then delete `remove`.

    Returns a dict of {Model.field: rows_moved}.
    """
    moved = {}
    with transaction.atomic():
        _fill_missing_scalar_fields(keep, remove)
        for rel in remove._meta.related_objects:
            if rel.many_to_many:
                # No M2M relations to Fighter today; skip defensively.
                continue
            related_model = rel.related_model
            fk_name = rel.field.name
            n = related_model.objects.filter(**{fk_name: remove}).update(
                **{fk_name: keep}
            )
            if n:
                moved[f"{related_model.__name__}.{fk_name}"] = n
        remove.delete()
    return moved


def label(f):
    return f"id={f.id} [{f.first_name} {f.last_name}] record=[{f.record}] fights={fight_count(f)}"


class Command(BaseCommand):
    help = "Find and merge duplicate Fighter records."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show exact-duplicate merges without applying them.",
        )
        parser.add_argument(
            "--candidates",
            action="store_true",
            help="List fuzzy duplicate candidates for manual review (no changes).",
        )
        parser.add_argument(
            "--merge",
            nargs=2,
            type=int,
            metavar=("KEEP_ID", "REMOVE_ID"),
            help="Manually merge REMOVE_ID into KEEP_ID.",
        )

    def handle(self, *args, **options):
        if options["merge"]:
            return self._manual_merge(*options["merge"])
        if options["candidates"]:
            return self._list_candidates()
        return self._merge_exact_duplicates(dry_run=options["dry_run"])

    # --- manual merge -----------------------------------------------------
    def _manual_merge(self, keep_id, remove_id):
        if keep_id == remove_id:
            raise CommandError("KEEP_ID and REMOVE_ID must differ.")
        try:
            keep = Fighter.objects.get(id=keep_id)
            remove = Fighter.objects.get(id=remove_id)
        except Fighter.DoesNotExist as e:
            raise CommandError(str(e))
        self.stdout.write(f"Keep:   {label(keep)}")
        self.stdout.write(f"Remove: {label(remove)}")
        moved = merge_fighters(keep, remove)
        self.stdout.write(self.style.SUCCESS(f"Merged. Repointed: {moved or 'nothing'}"))

    # --- exact duplicates -------------------------------------------------
    def _merge_exact_duplicates(self, dry_run):
        groups = (
            Fighter.objects.annotate(_full=normalized_full_name_expr())
            .values("_full")
            .annotate(c=Count("id"))
            .filter(c__gt=1)
        )
        full_names = [g["_full"] for g in groups]
        if not full_names:
            self.stdout.write(self.style.SUCCESS("No exact-duplicate full names found."))
            return

        total_merged = 0
        for full in full_names:
            dupes = list(
                Fighter.objects.annotate(_full=normalized_full_name_expr()).filter(
                    _full=full
                )
            )
            # Keep the one with the most fights (ties -> lowest id).
            dupes.sort(key=lambda f: (-fight_count(f), f.id))
            keep, removes = dupes[0], dupes[1:]
            self.stdout.write(f"\n'{full}': keep {label(keep)}")
            for r in removes:
                self.stdout.write(f"   merge  {label(r)}")
                if not dry_run:
                    merge_fighters(keep, r)
                    total_merged += 1

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f"\nDRY RUN - {len(full_names)} duplicate name group(s) would be merged. "
                    "Re-run without --dry-run to apply."
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f"\nMerged {total_merged} duplicate fighter(s).")
            )

    # --- fuzzy candidates -------------------------------------------------
    def _list_candidates(self):
        by_last = defaultdict(list)
        for f in Fighter.objects.all():
            by_last[(f.last_name or "").strip().lower()].append(f)

        found = 0
        for last, group in by_last.items():
            if not last or len(group) < 2:
                continue
            for i in range(len(group)):
                for j in range(i + 1, len(group)):
                    a, b = group[i], group[j]
                    fa = (a.first_name or "").lower().strip()
                    fb = (b.first_name or "").lower().strip()
                    if not fa or not fb or fa == fb:
                        continue
                    # Flag only when one first name is a prefix of the other
                    # (chris/christian, cam/cameron, billy/billy ray). Merely
                    # sharing a first token (jong wang / jong won / jong man) is
                    # too loose - those are usually different people.
                    if fa.startswith(fb) or fb.startswith(fa):
                        found += 1
                        self.stdout.write(f"\nPossible duplicate:")
                        self.stdout.write(f"   {label(a)}")
                        self.stdout.write(f"   {label(b)}")
                        keep, remove = (a, b) if fight_count(a) >= fight_count(b) else (b, a)
                        self.stdout.write(
                            f"   -> review: python manage.py dedup_fighters --merge {keep.id} {remove.id}"
                        )

        if not found:
            self.stdout.write(self.style.SUCCESS("No fuzzy duplicate candidates found."))
        else:
            self.stdout.write(
                self.style.WARNING(
                    f"\n{found} candidate pair(s). These are NOT auto-merged - "
                    "review and merge the real ones with --merge."
                )
            )
