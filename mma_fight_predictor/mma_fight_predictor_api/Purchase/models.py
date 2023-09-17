from django.db import models
from django.contrib.auth.models import User

class Purchase(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    purchase_date = models.DateTimeField()
    is_yearly_subscription = models.BooleanField(default=False)
    event_name = models.CharField(max_length=255)  # Store the name or identifier of the event

    def __str__(self):
        return f"{self.user.username} - {self.event_name} ({'Yearly' if self.is_yearly_subscription else 'Single Event'})"
