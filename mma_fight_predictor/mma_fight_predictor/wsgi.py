"""
WSGI config for mma_fight_predictor project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.0/howto/deployment/wsgi/
"""

import os
import sys
from django.core.wsgi import get_wsgi_application
# sys.path.append('/mma_fight_predictor')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mma_fight_predictor.mma_fight_predictor.settings')


application = get_wsgi_application()
