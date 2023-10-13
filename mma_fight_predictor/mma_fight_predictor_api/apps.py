from django.apps import AppConfig
import os
import sys
class MmaFightPredictorApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    # name = 'mma_fight_predictor.mma_fight_predictor_api'
    if 'makemigrations' not in sys.argv and 'migrate' not in sys.argv and 'showmigrations' not in sys.argv:
      name = 'mma_fight_predictor.mma_fight_predictor_api'
    else:
      name =  'mma_fight_predictor_api'
    # if os.environ.get('ENV') == "PROD":
    #   name = 'mma_fight_predictor.mma_fight_predictor_api' # PROD
    # else:
    #   name = 'mma_fight_predictor_api'
