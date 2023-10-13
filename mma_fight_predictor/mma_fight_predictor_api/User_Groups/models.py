from django.db import models
from django.contrib.auth.models import User

class User_Groups(models.Model):
    groups: models.CharField(max_length=30, blank=True)
