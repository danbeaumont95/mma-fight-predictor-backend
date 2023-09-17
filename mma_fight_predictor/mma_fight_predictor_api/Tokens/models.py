from django.db import models
from django.contrib.auth.models import User

class Token(models.Model):
  user = models.ForeignKey(User, on_delete=models.CASCADE)
  refresh_token = models.CharField(max_length=600, blank=True)
  access_token = models.CharField(max_length=600, blank=True)
  
  def __str__(self) -> str:
    return f"{self.user.email}"
