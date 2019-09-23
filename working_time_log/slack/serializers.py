from rest_framework import serializers

from slack.models import Users


class SlackEnterSerializer(serializers.ModelSerializer):

    class Meta:
        model = Users
        fields = ['username']
