#!/bin/bash
# Monthly: retrain the win-probability model on the latest data.
PROJ="/Users/danbeaumont95/Desktop/Python-Projects/mma-fight-predictor/mma_fight_predictor"
cd "$PROJ" || exit 1
source ../django_env/bin/activate
mkdir -p logs
echo "===== retrain $(date) =====" >> logs/retrain.log
python manage.py train_win_model >> logs/retrain.log 2>&1
