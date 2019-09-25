from django.db import models


class WorkLogs(models.Model):
    username = models.CharField(max_length=40)
    entered_time = models.DateTimeField(null=True)
    exited_time = models.DateTimeField(null=True)
    break_hours = models.DecimalField(default=0, max_digits=4, decimal_places=3, null=True)
    random_id = models.CharField(max_length=10)
    total_hours = models.DecimalField(max_digits=5, decimal_places=3, null=True)
