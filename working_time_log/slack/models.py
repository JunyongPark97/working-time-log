from django.db import models

# Create your models here.

class Users(models.Model):
    username = models.CharField(max_length=40)
    entered_time = models.DateTimeField(null=True)
    exited_time = models.DateTimeField(null=True)
    break_hours = models.IntegerField(default=0, null=True)
