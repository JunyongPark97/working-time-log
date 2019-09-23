import copy
import json, random, string
import requests
from django.http import HttpResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from rest_framework.response import Response
from requests.compat import basestring
from rest_framework import status
from urllib.parse import unquote
from rest_framework.generics import GenericAPIView
from working_time_log.loader import load_credential

from slack.serializers import SlackEnterSerializer

from slack.models import Users


class WebHookEnter(GenericAPIView):
    serializer_class = SlackEnterSerializer
    # permission_classes =
    queryset = Users.objects.all()

    def post(self, request):
        user = self.get_username()
        random_id = self._make_random_id()
        enter_time = timezone.now()
        text = request.body.decode("utf-8").split('&')[8].split('=')[1]

        if len(text) > 5:
            y, m, r_id = self.get_info(text)
            re_time = y + ' ' + m
            instance = Users.objects.filter(username=user, random_id=r_id).first()
            if not instance:
                self.slack_message('없는 ID 입니다.')
                return Response(status=status.HTTP_204_NO_CONTENT)
            origin_time = instance.entered_time
            if not instance.entered_time:
                self.slack_message('해당 ID 는 출근시간이 없습니다.')
                return Response(status=status.HTTP_204_NO_CONTENT)
            instance.entered_time = re_time
            instance.save()
            self.slack_message('출근시간 업데이트 되었습니다. {} --> {}'.format(origin_time, re_time))
            return Response(status=status.HTTP_206_PARTIAL_CONTENT)

        Users.objects.create(username=user, entered_time=enter_time, random_id=random_id)
        incomming_url = load_credential("SLACK_INCOMMING_URL")
        post_data = {"text": 'hello {}, 출근시각 {}'.format(user, enter_time), "attachments": [{"text": "welcome! today's id is --> {}".format(random_id)}]}
        data = json.dumps(post_data)
        headers = {'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8'}
        response = requests.post(incomming_url, headers=headers, data=data)
        return Response(status=status.HTTP_200_OK)

    def get_username(self):
        body = self.request.body.decode("utf-8")
        username = body.split('&')[6].split('=')[1]
        return username

    def _make_random_id(self):
        key_source = string.ascii_letters + string.digits
        random_id = ''.join(random.choice(key_source) for _ in range(6))
        return random_id

    def get_info(self, text):
        datas = text.split('+')
        print(len(datas))
        year = []
        r_id = []
        for data in datas:
            if '2019' in data:
                year = data
                datas.pop(datas.index(data))
            if len(data) == 6:
                r_id = data
                datas.pop(datas.index(data))
        print(datas)
        data = datas[0].replace("%3A",":",2)
        return year, data, r_id

    def slack_message(self, message):
        incomming_url = load_credential("SLACK_INCOMMING_URL")
        post_data = {"text": '{}'.format(message)}
        data = json.dumps(post_data)
        headers = {'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8'}
        response = requests.post(incomming_url, headers=headers, data=data)
        return None


class WebHookExit(GenericAPIView):
    # serializer_class = SlackEnterSerializer
    # permission_classes =
    queryset = Users.objects.all()

    def post(self, request):
        user = self.get_username()
        exit_time = timezone.now()
        text = request.body.decode("utf-8").split('&')[8].split('=')[1]
        if not len(text) > 5 :
            self.slack_message('데이터를 입력해주세요')
            return Response(status=status.HTTP_204_NO_CONTENT)

        if len(text.split('+')) == 4:
            #정정 입력 : 년월일, 시간, -breaking_time, id
            y, m, b_time, r_id = self.get_re_info(text)
            instance = Users.objects.filter(username=user, random_id=r_id).first()
            if not instance:
                # 해당 id 가 없는 경우
                self.slack_message('없는 ID 입니다.')
                return Response(status=status.HTTP_204_NO_CONTENT)
            re_time = y + ' ' + m
            exit_time = instance.exited_time
            instance.exited_time = re_time
            instance.break_hours = b_time
            instance.save()
            self.slack_message('{}님, 퇴근시각 변경 {} --> {} 오늘도 수고하셨습니다 :)'.format(user, exit_time, re_time))

        if len(text.split('+')) == 2:
            # 정상 입력 : -breaking_time, id
            b_time, r_id = self.get_info(text)
            instance = Users.objects.filter(username=user, random_id=r_id).first()
            if not instance:
                # 해당 id 가 없는 경우
                self.slack_message('없는 ID 입니다.')
                return Response(status=status.HTTP_204_NO_CONTENT)
            Users.objects.update_or_create(username=user, random_id=r_id, defaults={'exited_time':exit_time, 'break_hours':b_time})
            self.slack_message('{}님, 퇴근시각 {} 오늘도 수고하셨습니다 :)'.format(user,exit_time))

        return Response(status=status.HTTP_200_OK)

    def get_username(self):
        body = self.request.body.decode("utf-8")
        username = body.split('&')[6].split('=')[1]
        return username

    def get_info(self,text):
        datas = text.split('+')
        r_id = []
        for data in datas:
            if len(data) == 6:
                r_id = data
                datas.pop(datas.index(data))
        return datas[0], r_id

    def get_re_info(self,text):
        datas = text.split('+')
        year = []
        re_time = []
        r_id = []
        for data in datas:
            if '2019' in data:
                year = data
                datas.pop(datas.index(data))
            if len(data) == 6:
                r_id = data
                datas.pop(datas.index(data))
        for data in datas:
            if '%3A' in data:
                re_time = data
                datas.pop(datas.index(data))
        re_time = re_time.replace("%3A",":",2)
        data = datas[0]
        return year, re_time, data, r_id

    def slack_message(self, message):
        incomming_url = load_credential("SLACK_INCOMMING_URL")
        post_data = {"text": '{}'.format(message)}
        data = json.dumps(post_data)
        headers = {'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8'}
        response = requests.post(incomming_url, headers=headers, data=data)
        return None


class WebHookExplanation(GenericAPIView):
    def get(self, request):
        incomming_url = load_credential("SLACK_INCOMMING_URL")
        post_data = {"text": '사용법! 띄어쓰기 주의',
                     "attachments": [{"text": "출근시 \n /출근   --> 오늘의 Id를 반환합니다. 반환된 Id로 정정시 사용합니다."
                                              "\n (출근 정정하고싶을때) /출근 2019-xx-xx 10:30:00 Id   --> 순서 주의, Id 꼭 써주세요."
                                              "\n 퇴근시 \n /퇴근 -2 Id   --> -2는 쉬었던 시간, 출근시 받았던 Id 꼭 써주세요."
                                              "\n (퇴근 정정하고 싶을때) /퇴근 2019-xx-xx 19:30:00 -2 Id   --> 순서주의, 쉬었던 시간, Id 꼭 써주세요"}]}
        data = json.dumps(post_data)
        headers = {'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8'}
        response = requests.post(incomming_url, headers=headers, data=data)
        return Response(status=status.HTTP_200_OK)