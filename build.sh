#!/usr/bin/env bash
set -o errexit  # exit on error
pip install -r requirements.txt
cd mma_fight_predictor/
python manage.py makemigrations
python manage.py migrate
