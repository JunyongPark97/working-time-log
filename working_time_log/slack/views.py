import json, random, string
import requests
from django.views.generic import TemplateView
from rest_framework.response import Response
from collections import OrderedDict
from rest_framework import status
from rest_framework.generics import GenericAPIView
from slack.tools import get_real_name, calculate_working_hours, get_week_data
from working_time_log.loader import load_credential
import datetime
from slack.models import WorkLogs


class WebHookEnter(GenericAPIView):
    queryset = WorkLogs.objects.all()

    def post(self, request):
        user = self.get_username()
        random_id = self._make_random_id()
        enter_time = datetime.datetime.now()
        enter_time = enter_time.strftime('%Y-%m-%d %H:%M:%S')
        text = request.body.decode("utf-8").split('&')[8].split('=')[1]
        y, m, r_id = self.get_info(text)

        if len(text) > 5:

            instance = self.get_queryset().filter(username=user, random_id=r_id).last()

            if not instance:
                self.slack_message('없는 ID 입니다.')
                return Response(status=status.HTTP_204_NO_CONTENT)

            if not instance.entered_time:
                self.slack_message('해당 ID 는 출근시간이 없습니다.')
                return Response(status=status.HTTP_204_NO_CONTENT)

            re_time = y + ' ' + m
            instance.entered_time = re_time
            instance.save()

            origin_time = instance.entered_time

            self.slack_message('출근시간 업데이트 되었습니다. {} --> {}'.format(origin_time, re_time))
            return Response(status=status.HTTP_206_PARTIAL_CONTENT)

        # create work log
        WorkLogs.objects.create(username=user, entered_time=enter_time, random_id=random_id)

        # slack message
        incomming_url = load_credential("SLACK_INCOMMING_URL")
        username = get_real_name(user)
        post_data = {"text": '안녕하세요 {}!, 좋은 아침입니다 :) 출근시각 {}'.format(username, enter_time), "attachments": [{"text": "오늘의 id --> {}".format(random_id)}]}
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
        year = []
        r_id = []
        for data in datas:
            if '2019' in data:
                year = data
                datas.pop(datas.index(data))
            if len(data) == 6:
                r_id = data
                datas.pop(datas.index(data))
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
    queryset = WorkLogs.objects.all()

    def post(self, request):
        user = self.get_username()
        exit_time = datetime.datetime.now()
        exit_time = exit_time.strftime('%Y-%m-%d %H:%M:%S')
        text = request.body.decode("utf-8").split('&')[8].split('=')[1]
        if not len(text) > 5 :
            self.slack_message('잘못된 입력입니다. "/사용법" 을 참고해주세요 :)')
            return Response(status=status.HTTP_204_NO_CONTENT)

        if len(text.split('+')) == 4:
            #정정 입력 : 년월일, 시간, -breaking_time, id
            y, m, b_time, r_id = self.get_re_info(text)
            instance = self.get_queryset().filter(username=user, random_id=r_id).last()
            if not instance:
                # 해당 id 가 없는 경우
                self.slack_message('없는 ID 입니다.')
                return Response(status=status.HTTP_204_NO_CONTENT)

            re_time = y + ' ' + m
            exit_time = instance.exited_time
            enter_time = instance.entered_time
            instance.exited_time = re_time
            instance.break_hours = b_time
            instance.total_hours = calculate_working_hours(enter_time, re_time, b_time)
            instance.save()
            username = get_real_name(user)
            self.slack_message('{}님, 퇴근시각 변경되었습니다. {} --> {} 오늘도 수고하셨습니다 :)'.format(username, exit_time, re_time))

        if len(text.split('+')) == 2:
            # 정상 입력 : -breaking_time, id
            b_time, r_id = self.get_info(text)
            instance = self.get_queryset().filter(username=user, random_id=r_id).last()
            if not instance:
                # 해당 id 가 없는 경우
                self.slack_message('없는 ID 입니다.')
                return Response(status=status.HTTP_204_NO_CONTENT)

            en_time = instance.entered_time
            instance.exited_time = exit_time
            instance.break_hours = b_time
            instance.total_hours = calculate_working_hours(en_time, exit_time, b_time)
            instance.save()
            username = get_real_name(user)
            self.slack_message('{}, 퇴근시각 {}  오늘도 수고하셨습니다 :)'.format(username, exit_time))

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
        post_data = {"text": '사용법! 띄어쓰기 주의\n 이번주 기록 확인 :"https://p1glujg9ma.execute-api.ap-northeast-2.amazonaws.com/dev"',
                     "attachments": [{"text": "출근시 \n /출근   --> 오늘의 Id를 반환합니다. 반환된 Id로 정정시 사용합니다."
                                              "\n (출근 정정하고싶을때) /출근 2019-xx-xx 10:30:00 Id   --> 순서 주의, Id 꼭 써주세요."
                                              "\n 퇴근시 \n /퇴근 -2 Id   --> -2는 쉬었던 시간, 출근시 받았던 Id 꼭 써주세요."
                                              "\n (퇴근 정정하고 싶을때) /퇴근 2019-xx-xx 19:30:00 -2 Id   --> 순서주의, 쉬었던 시간, Id 꼭 써주세요"}]}
        data = json.dumps(post_data)
        headers = {'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8'}
        response = requests.post(incomming_url, headers=headers, data=data)
        return Response(status=status.HTTP_200_OK)


class ChartView(TemplateView):
    template_name = "home.html"

    def get_context_data(self):
        context = super().get_context_data()
        context['chart'] = self.working_chart()
        return context

    def working_chart(self):
        jun_queryset = WorkLogs.objects.filter(username='pjyong68')
        sang_queryset = WorkLogs.objects.filter(username='dltkddn0323')
        shin_queryset = WorkLogs.objects.filter(username='shimdw2')

        # get total data
        total_data = {}
        total_data['준용'] = get_week_data(jun_queryset)
        total_data['상우'] = get_week_data(sang_queryset)
        total_data['찬영'] = get_week_data(shin_queryset)

        # ordering
        ordered = OrderedDict(sorted(total_data.items(), key=lambda i: i[1]['total'], reverse=True))
        total_data = dict(ordered)

        return total_data
