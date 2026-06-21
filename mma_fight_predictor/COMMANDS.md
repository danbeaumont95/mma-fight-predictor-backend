# MMA Fight Predictor — Command Reference

All commands run from this directory (`mma_fight_predictor/`, where `manage.py` lives).

```bash
cd /Users/danbeaumont95/Desktop/Python-Projects/mma-fight-predictor/mma_fight_predictor
source ../django_env/bin/activate     # activate the virtualenv first, every session
```

Local Postgres must be running (creds come from `.env`: `DB_NAME` / `DB_USER` / `DB_PASSWORD`).

---

## 1. Setup / sanity

```bash
python manage.py migrate          # apply DB migrations (safe no-op if up to date)
python manage.py check            # should print "System check identified no issues"
python manage.py runserver        # start the API locally at http://localhost:8000
```

> Note: locally the app loads under the `ENV != "PROD"` branch. Production sets `ENV=PROD`.

---

## 2. Data pipeline (scrape ufcstats.com)

### `backfill_data` — scrape fighters and fights

```bash
# Full refresh: refresh existing fighters' stats + add new, then all fights
python manage.py backfill_data --update-existing

# Add only brand-new fighters (don't re-fetch existing), then all fights
python manage.py backfill_data

# Fighters only / fights only
python manage.py backfill_data --fighters-only --update-existing
python manage.py backfill_data --fights-only

# FAST incremental update after a card — only scan the newest N events
python manage.py backfill_data --fights-only --recent 2     # ~seconds

# Mimic the old endpoint (skip the 2 newest events)
python manage.py backfill_data --skip-recent 2
```

| Flag | Effect |
|------|--------|
| `--fighters-only` | Scrape fighters, skip fights |
| `--fights-only` | Scrape fights, skip fighters |
| `--update-existing` | Re-fetch stats for fighters already in the DB (slow: one request per fighter) |
| `--recent N` | Only scan the newest N completed events (fast incremental update) |
| `--skip-recent N` | Skip the newest N events (default 0) |

> Without `--recent`, the fight scraper crawls the **entire** event history (1994→today) every run — minutes. Use `--recent 2` for routine post-card updates.
> Scrape errors are appended to `errors-4.txt`.

### `dedup_fighters` — merge duplicate fighter records

```bash
python manage.py dedup_fighters --dry-run        # preview exact-name duplicates
python manage.py dedup_fighters                  # merge exact duplicates
python manage.py dedup_fighters --candidates     # list fuzzy pairs to review (no changes)
python manage.py dedup_fighters --merge 959 958  # keep id 959, fold id 958 into it
```

- **Exact duplicates** (identical full name) are merged automatically.
- **Fuzzy candidates** (e.g. `chris duncan` vs `christian leroy duncan`) are only *listed* — review and merge real ones manually with `--merge KEEP_ID REMOVE_ID`. They are NOT all guaranteed duplicates.
- Merging repoints all foreign keys (fights, etc.) and fills empty fields on the kept row before deleting.

---

## 3. Machine learning

### `train_win_model` — train the win-probability model

```bash
python manage.py train_win_model                       # train + evaluate + save best model
python manage.py train_win_model --cutoff 2023-01-01   # change train/test split date
python manage.py train_win_model --min-prior 4         # require >= N prior fights per fighter
```

Builds point-in-time features, does a time-based train/test split, trains a logistic-regression
baseline + a gradient booster, prints metrics (accuracy / log loss / ROC AUC / Brier) vs the
existing heuristic, and saves the better model to `mma_fight_predictor_api/ml/models/win_model.joblib`.
Re-run after a data refresh to retrain on the latest fights.

### `predict_fight` — predict a single matchup

```bash
python manage.py predict_fight "Islam Makhachev" "Charles Oliveira"
python manage.py predict_fight "Manel Kape" "Kyoji Horiguchi"
```

Returns each fighter's win probability and the model's pick. Names are matched
accent/format-tolerantly; unknown fighters raise a clear error.

### `score_predictions` — score saved predictions vs results

```bash
python manage.py score_predictions          # score newly-resolved predictions
python manage.py score_predictions --all     # re-score everything
```

Matches each saved `ModelPrediction` to its real fight, records the actual
winner + whether the pick was correct, and prints overall accuracy plus a
calibration table (does "70%" really win ~70% of the time?). Run it after
`backfill_data --fights-only --recent 2` so the results are in the DB.

### HTTP endpoint — `POST /mma_fight_predictor/predict_fight`

```bash
python manage.py runserver
curl -X POST http://localhost:8000/mma_fight_predictor/predict_fight \
  -H "Content-Type: application/json" \
  -d '{"fighter_a":"Manel Kape","fighter_b":"Kyoji Horiguchi"}'
```

Returns win probabilities for the matchup (model + accumulators are cached and
auto-refresh after a data update). Add `"save": true` (and optionally
`"event_date": "YYYY-MM-DD"`) to log the prediction to `ModelPrediction` for
later scoring; it returns a `prediction_id`. Casual lookups without `save` are
not persisted.

---

## 4. Per-card predict → score workflow

Predict a card the night before, then score it against real results in the morning.
(`predict_tonight.py` holds the card; edit it for the next event.)

```bash
# Evening: generate + save predictions to predictions_ufc_<date>.json
python manage.py shell -c "exec(open('predict_tonight.py').read())"

# Morning: ingest results, then score the predictions
python manage.py backfill_data --fights-only --recent 2
python manage.py shell -c "exec(open('score_tonight.py').read())"
```

`score_tonight.py` prints per-fight ✓/✗ and overall accuracy, and writes the actual
winners back into the JSON file.

---

## 5. Handy inspection snippets

```bash
# DB counts + latest fight
python manage.py shell -c "from mma_fight_predictor_api.Fighter.models import Fighter; from mma_fight_predictor_api.Fights.models import Fight; print('fighters', Fighter.objects.count(), '| fights', Fight.objects.count(), '| latest', Fight.objects.order_by('-date').values_list('date', flat=True).first())"

# Inspect the saved model
python manage.py shell -c "import joblib; m=joblib.load('mma_fight_predictor_api/ml/models/win_model.joblib'); print(m['model_name'], m['trained_at']); print(m['features'])"
```

> In `shell -c \"...\"`, keep everything on one line with `;` separators — indented blocks raise `IndentationError`.

---

## File map

| Path | What |
|------|------|
| `mma_fight_predictor_api/management/commands/` | `backfill_data`, `dedup_fighters`, `train_win_model`, `predict_fight` |
| `mma_fight_predictor_api/ml/features.py` | Point-in-time feature engineering |
| `mma_fight_predictor_api/ml/predict.py` | `predict_matchup()` |
| `mma_fight_predictor_api/ml/models/win_model.joblib` | Saved model (regenerated by `train_win_model`) |
| `mma_fight_predictor_api/helpers/scraping.py` | ufcstats scrapers (+ JS proof-of-work gate solver in `helpers.py`) |
| `predict_tonight.py` / `score_tonight.py` | Per-card predict + score scripts |
