from django.db import models


class User(models.Model):
    username = models.CharField(max_length=40)
    korean_name = models.CharField(max_length=30)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.korean_name


class WorkLogs(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='logs')
    entered_time = models.DateTimeField(null=True)
    exited_time = models.DateTimeField(null=True)
    break_hours = models.DecimalField(default=0, max_digits=4, decimal_places=3, null=True)
    random_id = models.CharField(max_length=10)
    total_hours = models.DecimalField(max_digits=5, decimal_places=3, null=True)

    is_user = models.BooleanField(null=True, blank=True)


class Slogan(models.Model):
    title = models.CharField(max_length=100)
    body = models.TextField(default='')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
