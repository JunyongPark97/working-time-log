from rest_framework import serializers
from slack.models import WorkLogs


class SlackEnterSerializer(serializers.ModelSerializer):

    class Meta:
        model = WorkLogs
        fields = ['username', 'entered_time']
