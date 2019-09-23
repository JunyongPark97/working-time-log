import copy
import json, random, string
import requests
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone
# Create your views here.
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from rest_framework.response import Response
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
        user = self.get_username()
        random_id = self._make_random_id()
        Users.objects.create(username=user, entered_time=timezone.now(), random_id=random_id)
        
        incomming_url = load_credential("SLACK_INCOMMING_URL")
        post_data = {"text": 'hello {}'.format(user),"attachments": [{"text": "welcome! today's id is {}".format(random_id)}]}
        data = json.dumps(post_data)
        headers = {'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8'}
        response = requests.post(incomming_url, headers=headers, data=data)

        return Response(status=status.HTTP_200_OK)

    def get_username(self):
        body = self.request.body.decode("utf-8")
        username = body.split('&')[6].split('=')[1]
        print(type(username))
        return username

    def _make_random_id(self):
        key_source = string.ascii_letters + string.digits
        random_id = ''.join(random.choice(key_source) for _ in range(6))
        return random_id
