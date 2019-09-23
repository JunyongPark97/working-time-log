import copy
import json

from django.http import HttpResponse
from django.shortcuts import render

# Create your views here.
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from requests.compat import basestring
from slacker import Slacker
# from slackclient import SlackClient
# from slack import WebClient
import time
import websocket

from working_time_log.loader import load_credential

slack_token = load_credential("SLACK_TOKEN")
# sc = WebClient(slack_token)
#
# def notification(message):
#     token = slack_token
#     slack = Slacker(token)
#     print(slack)
#     slack.chat.post_message('#working_time', message)
#
# if sc.rtm_connect():
#     print('---')
#     while True:
#         receive_data = sc.rtm_read()
#
#         if len(receive_data):
#             keys = list(receive_data[0].keys())
#             if 'type' in keys and 'text' in keys:
#                 print(receive_data[0]['text'])
#                 message = receive_data[0]['text']
#                 notification(message + 'oooo')
#         time.sleep(1)
# else:
#     print("Failed")

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