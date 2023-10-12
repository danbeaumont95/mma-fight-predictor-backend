from django.db import models

class Fighter(models.Model):
  first_name = models.CharField(max_length=40, blank=True)
  last_name = models.CharField(max_length=40, blank=True, null=True)
  gender = models.CharField(max_length=6, blank=True)
  style = models.CharField(max_length=30, blank=True, null=True)
  record = models.CharField(max_length=30, blank=True)
  height = models.CharField(max_length=20, blank=True)
  stance = models.CharField(max_length=20, blank=True)
  dob = models.CharField(max_length=20, blank=True)
  weight = models.CharField(max_length=20, blank=True)
  reach = models.CharField(max_length=20, blank=True)
  slpm = models.FloatField(default=0.0)
  str_acc = models.CharField(max_length=5, blank=True)
  sapm = models.FloatField(default=0.0)
  str_def = models.CharField(max_length=5, blank=True)
  td_avg = models.FloatField(default=0.0)
  td_acc = models.CharField(max_length=5, blank=True)
  td_def = models.CharField(max_length=5, blank=True)
  sub_avg = models.FloatField(default=0.0)
  
  def __str__(self) -> str:
    return super().__str__()
  
  def get_full_name(self):
    return f"{self.first_name} {self.last_name}"
