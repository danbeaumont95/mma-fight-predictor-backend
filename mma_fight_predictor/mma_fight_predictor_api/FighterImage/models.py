# models.py
from django.db import models
from ..Fighter.models import Fighter

class Image(models.Model):
    fighter = models.ForeignKey(Fighter, on_delete=models.DO_NOTHING, related_name='fighter')
    image_data = models.BinaryField()
    created_at = models.DateTimeField(auto_now_add=True)
