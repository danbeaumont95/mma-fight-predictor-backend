#!/bin/bash
# Saturday (pre-card): predict + save the next upcoming UFC card.
PROJ="/Users/danbeaumont95/Desktop/Python-Projects/mma-fight-predictor/mma_fight_predictor"
cd "$PROJ" || exit 1
source ../django_env/bin/activate
mkdir -p logs
echo "===== predict_upcoming $(date) =====" >> logs/predict_card.log
python manage.py predict_upcoming >> logs/predict_card.log 2>&1
