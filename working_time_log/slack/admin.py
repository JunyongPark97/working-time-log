# Register your models here.
from django.contrib import admin

from slack.models import User, WorkLogs, Slogan


class UserAdmin(admin.ModelAdmin):
    list_display = ['id', 'username', 'korean_name', 'is_active']
    list_editable = ['is_active']

class WorkLogsAdmin(admin.ModelAdmin):
    list_display = ['user', 'entered_time', 'exited_time', 'break_hours', 'random_id', 'total_hours']

class SloganAdmin(admin.ModelAdmin):
    list_display = ['title', 'body','is_active']

admin.site.register(User, UserAdmin)
admin.site.register(WorkLogs, WorkLogsAdmin)
admin.site.register(Slogan, SloganAdmin)
