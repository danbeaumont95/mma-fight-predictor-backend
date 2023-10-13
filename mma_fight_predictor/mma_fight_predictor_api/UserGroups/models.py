from django.db import models
from django.contrib.auth.models import User

class UserGroups(models.Model):
    groups: models.CharField(max_length=30, blank=True)
