from django.db import models
from ..Fighter.models import Fighter

class Fight(models.Model):
  red_fighter = models.ForeignKey(Fighter, on_delete=models.DO_NOTHING, related_name='red_fighter')
  blue_fighter = models.ForeignKey(Fighter, on_delete=models.DO_NOTHING, related_name='blue_fighter')
  r_kd = models.IntegerField(blank=True, null=True)
  b_kd = models.IntegerField(blank=True, null=True)
  r_sig_str = models.CharField(max_length=30, blank=True, null=True)
  b_sig_str = models.CharField(max_length=30, blank=True, null=True)
  r_sig_str_pct = models.CharField(max_length=30, blank=True, null=True)
  b_sig_str_pct = models.CharField(max_length=30, blank=True, null=True)
  r_total_str = models.CharField(max_length=30, blank=True, null=True)
  b_total_str = models.CharField(max_length=30, blank=True, null=True)
  r_td = models.CharField(max_length=30, blank=True, null=True)
  b_td = models.CharField(max_length=30, blank=True, null=True)
  r_td_pct = models.CharField(max_length=30, blank=True, null=True)
  b_td_pct = models.CharField(max_length=30, blank=True, null=True)
  r_sub_att = models.CharField(max_length=30, blank=True, null=True)
  b_sub_att = models.CharField(max_length=30, blank=True, null=True)
  r_rev = models.CharField(max_length=30, blank=True, null=True)
  b_rev = models.CharField(max_length=30, blank=True, null=True)
  r_ctrl = models.CharField(max_length=30, blank=True, null=True)
  b_ctrl = models.CharField(max_length=30, blank=True, null=True)
  r_head = models.CharField(max_length=30, blank=True, null=True)
  b_head = models.CharField(max_length=30, blank=True, null=True)
  r_body = models.CharField(max_length=30, blank=True, null=True)
  b_body = models.CharField(max_length=30, blank=True, null=True)
  r_leg = models.CharField(max_length=30, blank=True, null=True)
  b_leg = models.CharField(max_length=30, blank=True, null=True)
  r_distance = models.CharField(max_length=30, blank=True, null=True)
  b_distance = models.CharField(max_length=30, blank=True, null=True)
  r_clinch = models.CharField(max_length=30, blank=True, null=True)
  b_clinch = models.CharField(max_length=30, blank=True, null=True)
  r_ground = models.CharField(max_length=30, blank=True, null=True)
  b_ground = models.CharField(max_length=30, blank=True, null=True)
  win_by = models.CharField(max_length=30, blank=True, null=True)
  last_round = models.IntegerField(blank=True, null=True)
  last_round_time = models.CharField(max_length=30, blank=True, null=True)
  referee = models.CharField(max_length=40, blank=True, null=True)
  date = models.DateField(blank=True, null=True)
  location = models.CharField(max_length=80, blank=True, null=True)
  fight_type = models.CharField(max_length=80, blank=True, null=True)
  winner = models.CharField(max_length=80, blank=True, null=True)
  format = models.CharField(max_length=80, null=True, blank=True)
  loser = models.CharField(max_length=80, blank=True, null=True)
  def __str__(self) -> str:
    return super().__str__()
