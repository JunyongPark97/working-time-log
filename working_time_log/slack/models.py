from django.db import models

# Create your models here.

class Users(models.Model):
    username = models.CharField(max_length=40)
    entered_time = models.DateTimeField(null=True)
    exited_time = models.DateTimeField(null=True)
    break_hours = models.DecimalField(default=0, max_digits=4, decimal_places=3, null=True)
    random_id = models.CharField(max_length=10)
