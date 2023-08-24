from django.apps import AppConfig
import os

class MmaFightPredictorApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'mma_fight_predictor.mma_fight_predictor_api'
    # if os.environ.get('ENV') == "PROD":
    #   name = 'mma_fight_predictor.mma_fight_predictor_api' # PROD
    # else:
    #   name = 'mma_fight_predictor_api'
