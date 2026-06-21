"""
Point-in-time feature engineering for the win-probability model.

The golden rule here is NO LEAKAGE: a fight's features may only use
information available *before* that fight happened. We guarantee this by
streaming fights in chronological order and, for each fight, snapshotting both
fighters' accumulated history *before* folding that fight's result back in.

We also deliberately ignore the blue/red corner. In this dataset the scraper
stored the winner as the blue fighter almost every time, so the corner leaks
the outcome. Instead each fight's two fighters are randomly assigned to slots
A and B, the label is "did A win", and features are A-minus-B differences --
symmetric and balanced.
"""
from collections import defaultdict
from datetime import datetime, date

import pandas as pd

from ..Fights.models import Fight


# --- tolerant parsers for the string-stored stats ----------------------------
def landed_of(value):
    """'91 of 192' -> 91 (the landed count). None if unparseable."""
    if not value:
        return None
    try:
        return int(str(value).split("of")[0].strip())
    except (ValueError, IndexError):
        return None


def ctrl_seconds(value):
    """'1:32' -> 92 seconds. None if unparseable."""
    if not value:
        return None
    try:
        m, s = str(value).split(":")
        return int(m) * 60 + int(s)
    except (ValueError, IndexError):
        return None


def parse_reach(value):
    """'72.0\"' -> 72.0 inches. None if missing/'--'."""
    if not value:
        return None
    digits = "".join(c for c in str(value) if c.isdigit() or c == ".")
    try:
        return float(digits) if digits else None
    except ValueError:
        return None


def parse_height(value):
    """'5\\' 11\"' -> 71 inches. None if unparseable."""
    if not value or "'" not in str(value):
        return None
    try:
        feet, rest = str(value).split("'")
        inches = "".join(c for c in rest if c.isdigit())
        return int(feet) * 12 + (int(inches) if inches else 0)
    except (ValueError, IndexError):
        return None


def parse_dob(value):
    for fmt in ("%b %d, %Y", "%B %d, %Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(str(value).strip(), fmt).date()
        except (ValueError, TypeError):
            continue
    return None


FINISH_METHODS = ("KO/TKO", "Submission", "TKO - Doctor's Stoppage")


def _new_acc():
    return {
        "n": 0,
        "wins": 0,
        "finishes": 0,
        "streak": 0,            # +ve win streak, -ve loss streak
        "sig_landed": 0.0,
        "sig_absorbed": 0.0,
        "ctrl": 0.0,
        "td_landed": 0.0,
        "last_date": None,
    }


def _snapshot(acc, fighter, fight_date):
    """Pre-fight feature vector for one fighter from their prior history."""
    n = acc["n"]
    dob = parse_dob(fighter.dob)
    return {
        "experience": n,
        "win_rate": acc["wins"] / n if n else 0.5,
        "streak": acc["streak"],
        "finish_rate": acc["finishes"] / acc["wins"] if acc["wins"] else 0.0,
        "avg_sig_landed": acc["sig_landed"] / n if n else 0.0,
        "avg_sig_absorbed": acc["sig_absorbed"] / n if n else 0.0,
        "avg_ctrl": acc["ctrl"] / n if n else 0.0,
        "avg_td": acc["td_landed"] / n if n else 0.0,
        "layoff_days": (fight_date - acc["last_date"]).days if acc["last_date"] else None,
        "age": (fight_date - dob).days / 365.25 if dob else None,
        "reach": parse_reach(fighter.reach),
        "height": parse_height(fighter.height),
    }


def _update(acc, fight, is_blue, won, fight_date):
    """Fold a completed fight into a fighter's running accumulator."""
    if is_blue:
        landed, absorbed, td, ctrl = (
            landed_of(fight.b_sig_str), landed_of(fight.r_sig_str),
            landed_of(fight.b_td), ctrl_seconds(fight.b_ctrl),
        )
    else:
        landed, absorbed, td, ctrl = (
            landed_of(fight.r_sig_str), landed_of(fight.b_sig_str),
            landed_of(fight.r_td), ctrl_seconds(fight.r_ctrl),
        )
    acc["n"] += 1
    acc["sig_landed"] += landed or 0
    acc["sig_absorbed"] += absorbed or 0
    acc["td_landed"] += td or 0
    acc["ctrl"] += ctrl or 0
    if won:
        acc["wins"] += 1
        acc["streak"] = acc["streak"] + 1 if acc["streak"] > 0 else 1
        if fight.win_by in FINISH_METHODS:
            acc["finishes"] += 1
    else:
        acc["streak"] = acc["streak"] - 1 if acc["streak"] < 0 else -1
    acc["last_date"] = fight_date


def _resolve_winner(fight):
    """Return (winner_fighter, loser_fighter) or (None, None) for draws/NC."""
    w = (fight.winner or "").strip().lower()
    blue, red = fight.blue_fighter, fight.red_fighter
    if w == blue.get_full_name().strip().lower():
        return blue, red
    if w == red.get_full_name().strip().lower():
        return red, blue
    return None, None


FEATURE_KEYS = [
    "experience", "win_rate", "streak", "finish_rate", "avg_sig_landed",
    "avg_sig_absorbed", "avg_ctrl", "avg_td", "layoff_days", "age",
    "reach", "height",
]


def build_dataset(min_prior_fights=1, seed=42):
    """Return a DataFrame of one row per usable fight with A-minus-B difference
    features, a balanced `label` (1 if slot A won), and the fight `date`."""
    import random

    rng = random.Random(seed)
    acc = defaultdict(_new_acc)
    rows = []

    fights = (
        Fight.objects.exclude(winner__isnull=True)
        .exclude(winner__exact="")
        .exclude(date__isnull=True)
        .select_related("blue_fighter", "red_fighter")
        .order_by("date", "id")
    )

    for f in fights.iterator():
        winner, loser = _resolve_winner(f)
        if winner is None:
            continue

        win_feat = _snapshot(acc[winner.id], winner, f.date)
        lose_feat = _snapshot(acc[loser.id], loser, f.date)

        # Update accumulators AFTER snapshotting (this is what prevents leakage).
        _update(acc[winner.id], f, is_blue=(winner.id == f.blue_fighter_id), won=True, fight_date=f.date)
        _update(acc[loser.id], f, is_blue=(loser.id == f.blue_fighter_id), won=False, fight_date=f.date)

        if win_feat["experience"] < min_prior_fights or lose_feat["experience"] < min_prior_fights:
            continue

        # Randomly assign winner/loser to slots A/B so the label is balanced
        # and the corner can't leak the result.
        if rng.random() < 0.5:
            a, b, label = win_feat, lose_feat, 1
        else:
            a, b, label = lose_feat, win_feat, 0

        row = {f"d_{k}": _diff(a[k], b[k]) for k in FEATURE_KEYS}
        row["label"] = label
        row["date"] = f.date
        rows.append(row)

    return pd.DataFrame(rows)


def _diff(x, y):
    if x is None or y is None:
        return None
    return x - y


def compute_current_accumulators():
    """Stream the whole fight history and return each fighter's FINAL career
    accumulator (used to build features for an upcoming, not-yet-fought bout)."""
    acc = defaultdict(_new_acc)
    fights = (
        Fight.objects.exclude(winner__isnull=True)
        .exclude(winner__exact="")
        .exclude(date__isnull=True)
        .select_related("blue_fighter", "red_fighter")
        .order_by("date", "id")
    )
    for f in fights.iterator():
        winner, loser = _resolve_winner(f)
        if winner is None:
            continue
        _update(acc[winner.id], f, is_blue=(winner.id == f.blue_fighter_id), won=True, fight_date=f.date)
        _update(acc[loser.id], f, is_blue=(loser.id == f.blue_fighter_id), won=False, fight_date=f.date)
    return acc


def matchup_difference_features(fighter_a, fighter_b, acc, as_of=None):
    """A-minus-B difference feature vector (in FEATURE_KEYS order) for a
    hypothetical bout as of `as_of` (defaults to today). Missing values are
    returned as None -> the model pipeline imputes them."""
    as_of = as_of or date.today()
    fa = _snapshot(acc[fighter_a.id], fighter_a, as_of)
    fb = _snapshot(acc[fighter_b.id], fighter_b, as_of)
    return [_diff(fa[k], fb[k]) for k in FEATURE_KEYS]
