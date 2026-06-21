from django.db import models

# Ensure the ML prediction model is registered with this app.
from .ml.models import ModelPrediction  # noqa: F401,E402
