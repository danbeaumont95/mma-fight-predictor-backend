"""
Train a fighter win-probability model from the fight history.

    python manage.py train_win_model
    python manage.py train_win_model --cutoff 2024-01-01 --min-prior 3

Trains a logistic-regression baseline and a gradient-boosted model on
point-in-time features (see ml/features.py), evaluates them on a time-based
hold-out, compares against the existing heuristic predictor, and saves the
better model to ml/models/win_model.joblib.
"""
import os
from datetime import datetime

import joblib
import numpy as np
from django.core.management.base import BaseCommand

from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, brier_score_loss, log_loss, roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

try:
    from mma_fight_predictor.mma_fight_predictor_api.ml.features import build_dataset, FEATURE_KEYS
    from mma_fight_predictor.mma_fight_predictor_api.Prediction.models import Prediction
except ModuleNotFoundError:  # pragma: no cover - dev app label
    from mma_fight_predictor_api.ml.features import build_dataset, FEATURE_KEYS
    from mma_fight_predictor_api.Prediction.models import Prediction

MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "ml", "models")


class Command(BaseCommand):
    help = "Train and evaluate the fighter win-probability model."

    def add_arguments(self, parser):
        parser.add_argument("--cutoff", default="2024-01-01",
                            help="Fights on/after this date are the test set (YYYY-MM-DD).")
        parser.add_argument("--min-prior", type=int, default=2,
                            help="Require each fighter to have at least this many prior fights.")

    def handle(self, *args, **options):
        cutoff = datetime.strptime(options["cutoff"], "%Y-%m-%d").date()
        feat_cols = [f"d_{k}" for k in FEATURE_KEYS]

        self.stdout.write("Building point-in-time features...")
        df = build_dataset(min_prior_fights=options["min_prior"])
        self.stdout.write(f"  {len(df)} usable fights, {len(feat_cols)} features.")

        train = df[df["date"] < cutoff]
        test = df[df["date"] >= cutoff]
        if test.empty or train.empty:
            self.stderr.write(self.style.ERROR("Empty train or test split -- adjust --cutoff."))
            return
        self.stdout.write(f"  train: {len(train)} (pre-{cutoff})  |  test: {len(test)} ({cutoff}+)")

        X_train, y_train = train[feat_cols].to_numpy(dtype=float), train["label"].to_numpy()
        X_test, y_test = test[feat_cols].to_numpy(dtype=float), test["label"].to_numpy()

        # Baseline: logistic regression (needs imputation + scaling).
        logreg = make_pipeline(
            SimpleImputer(strategy="median"), StandardScaler(),
            LogisticRegression(max_iter=1000),
        ).fit(X_train, y_train)

        # Gradient boosting: handles NaN natively, captures interactions.
        gbm = HistGradientBoostingClassifier(
            max_iter=300, learning_rate=0.05, max_depth=4,
            l2_regularization=1.0, random_state=42,
        ).fit(X_train, y_train)

        self.stdout.write("\n" + self._header())
        self.stdout.write(self._row("coin-flip baseline", y_test, np.full(len(y_test), 0.5)))
        lr_metrics = self._row("logistic regression", y_test, logreg.predict_proba(X_test)[:, 1])
        gbm_metrics = self._row("gradient boosting", y_test, gbm.predict_proba(X_test)[:, 1])
        self.stdout.write(lr_metrics)
        self.stdout.write(gbm_metrics)

        self._report_heuristic()

        # Keep whichever model gives the better (lower) hold-out log loss.
        candidates = {"logistic_regression": logreg, "gradient_boosting": gbm}
        best_name = min(candidates, key=lambda k: self._logloss(candidates[k], X_test, y_test))
        best = candidates[best_name]

        os.makedirs(MODEL_DIR, exist_ok=True)
        path = os.path.normpath(os.path.join(MODEL_DIR, "win_model.joblib"))
        joblib.dump(
            {"model": best, "model_name": best_name, "features": feat_cols,
             "trained_at": datetime.now().isoformat(), "cutoff": str(cutoff),
             "n_train": len(train), "n_test": len(test)},
            path,
        )
        self.stdout.write(self.style.SUCCESS(f"\nSaved best model ({best_name}) -> {path}"))
        self.stdout.write(self._top_features(best, X_test, y_test, feat_cols))

    def _logloss(self, model, X_test, y_test):
        p = np.clip(model.predict_proba(X_test)[:, 1], 1e-6, 1 - 1e-6)
        return log_loss(y_test, p, labels=[0, 1])

    # --- reporting helpers -------------------------------------------------
    def _header(self):
        return f"{'model':22} {'accuracy':>9} {'log_loss':>9} {'roc_auc':>8} {'brier':>7}"

    def _row(self, name, y_true, p):
        p = np.clip(p, 1e-6, 1 - 1e-6)
        acc = accuracy_score(y_true, (p >= 0.5).astype(int))
        ll = log_loss(y_true, p, labels=[0, 1])
        try:
            auc = roc_auc_score(y_true, p)
        except ValueError:
            auc = float("nan")
        brier = brier_score_loss(y_true, p)
        return f"{name:22} {acc:9.3f} {ll:9.3f} {auc:8.3f} {brier:7.3f}"

    def _report_heuristic(self):
        qs = Prediction.objects.filter(did_prediction_winner_win__isnull=False)
        n = qs.count()
        if not n:
            self.stdout.write("\nHeuristic predictor: no labelled predictions to score.")
            return
        wins = qs.filter(did_prediction_winner_win=True).count()
        self.stdout.write(
            f"\nExisting heuristic predictor accuracy: {wins / n:.3f} "
            f"({wins}/{n} stored predictions, all dates)."
        )

    def _top_features(self, model, X_test, y_test, feat_cols):
        from sklearn.inspection import permutation_importance
        imp = permutation_importance(model, X_test, y_test, n_repeats=5, random_state=42, scoring="roc_auc")
        order = np.argsort(imp.importances_mean)[::-1][:6]
        lines = ["\nTop features (permutation importance):"]
        for i in order:
            lines.append(f"  {feat_cols[i]:18} {imp.importances_mean[i]:+.4f}")
        return "\n".join(lines)
