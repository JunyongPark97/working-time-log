import copy
import json

import requests
from django.http import HttpResponse
from django.shortcuts import render

# Create your views here.
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from requests import Response
from requests.compat import basestring
from rest_framework import status
from rest_framework.generics import GenericAPIView
from slacker import Slacker
# from slackclient import SlackClient
# from slack import WebClient
import time
import websocket

from working_time_log.loader import load_credential

from slack.serializers import SlackEnterSerializer

from slack.models import Users


@csrf_exempt
@require_POST
def webhook(request):
    jsondata = request.body
    print('---1')
    print(jsondata)
    data = json.loads(jsondata)
    print('---2')
    print(data)
    meta = copy.copy(request.META)
    print('---3')
    print(meta)
    for k,v in meta.items():
        if not isinstance(v, basestring):
            # del meta[k]
            print('Failed')
    return HttpResponse(status=200)

class WebHookTest(GenericAPIView):
    serializer_class = SlackEnterSerializer
    # permission_classes =
    queryset = Users.objects.all()

    def post(self, request):
        print(request.body)

        print(self.get_username())
        incomming_url = load_credential("SLACK_INCOMMING_URL")
        post_data = {
                    "text": "I am a test message http://slack.com",
                    "attachments": [
                                    {
                                        "text": "And here's an attachment!"
                                    }
                                    ]
                    }
        response = requests.post(incomming_url, data=post_data)
        content = response.content
        print('success')

        return Response(status=status.HTTP_200_OK)

    def get_username(self):
        body = self.request.body
        username = body.split('&')
        return username