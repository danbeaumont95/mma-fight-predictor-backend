#!/bin/bash
# Sunday (post-card): ingest the latest results, then score saved predictions.
PROJ="/Users/danbeaumont95/Desktop/Python-Projects/mma-fight-predictor/mma_fight_predictor"
cd "$PROJ" || exit 1
source ../django_env/bin/activate
mkdir -p logs
echo "===== score_card $(date) =====" >> logs/score_card.log
python manage.py backfill_data --fights-only --recent 2 >> logs/score_card.log 2>&1
python manage.py score_predictions >> logs/score_card.log 2>&1
