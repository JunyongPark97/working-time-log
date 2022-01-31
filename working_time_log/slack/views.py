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
from slack.models import WorkLogs, User, Slogan
from urllib import parse
import re

class WebHookEnter(GenericAPIView):
    queryset = WorkLogs.objects.all()

    def post(self, request):
        user = self.get_user()
        random_id = self._make_random_id()
        enter_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        text = request.body.decode("utf-8").split('&')[8].split('=')[1]

        if len(text) > 5:
            y, m, r_id = self.get_info(text)

            instance = self.get_queryset().filter(user=user, random_id=r_id).last()

            if not instance:
                self.slack_message('없는 ID 입니다.')
                return Response(status=status.HTTP_204_NO_CONTENT)

            if not instance.entered_time:
                self.slack_message('해당 ID 는 출근시간이 없습니다.')
                return Response(status=status.HTTP_204_NO_CONTENT)

            if y is None:
                y = instance.entered_time.strftime('%Y-%m-%d')

            re_time = y + ' ' + m
            origin_time = instance.entered_time
            instance.entered_time = re_time
            instance.is_user = True
            instance.save()

            self.slack_message('출근시간 업데이트 되었습니다. `\033{}\033`` --> `\033{}\033`'.format(origin_time, re_time))
            return Response(status=status.HTTP_206_PARTIAL_CONTENT)

        if user.logs.exists() and (not user.logs.last().exited_time or not user.logs.last().is_user):
            incomming_url = load_credential("SLACK_INCOMMING_URL")
            logs = user.logs.last()
            logs.exited_time = logs.entered_time + datetime.timedelta(hours=7)
            logs.save()  # 먼저 퇴근처리
            username = get_real_name(user)

            post_data = {"text": '어제 퇴근처리가 안되었습니다!',
                         "attachments" : [{"text":  "`\033/퇴근 2022-xx-xx (시간) -(쉬는시간) Id\033`"
                                                    "\n을 먼저 입력해주세요!"
                                                    "\n{}의 어제 아이디는 {}입니다.".format(username, logs.random_id)}]}
            data = json.dumps(post_data)
            headers = {'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8'}
            response = requests.post(incomming_url, headers=headers, data=data)
            return Response(status=status.HTTP_200_OK)


        # create work log
        WorkLogs.objects.create(user=user, entered_time=enter_time, random_id=random_id, is_user=True)

        # slack message
        incomming_url = load_credential("SLACK_INCOMMING_URL")
        username = get_real_name(user)
        post_data = {"text": '안녕하세요 {}!, 좋은 아침입니다 :) 출근시각 {}'.format(username, enter_time), "attachments": [{"text": "오늘의 id --> {}".format(random_id)}]}
        data = json.dumps(post_data)
        headers = {'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8'}
        response = requests.post(incomming_url, headers=headers, data=data)
        return Response(status=status.HTTP_200_OK)

    def get_user(self):
        body = self.request.body.decode("utf-8")
        username = body.split('&')[6].split('=')[1]
        user = User.objects.filter(username=username).last()
        return user

    def _make_random_id(self):
        key_source = string.ascii_letters + string.digits
        random_id = ''.join(random.choice(key_source) for _ in range(6))
        return random_id

    def get_info(self, text):
        datas = text.split('+')
        year = []
        r_id = []
        re_time = []
        if '2022' in datas[0]:
            year = datas[0]
            datas = datas[1:]
        else:
            year = None

        for data in datas:
            if len(data) == 6:
                r_id = data
                datas.pop(datas.index(data))

        if '%3A' in datas[0]:  # "10:00:00 or 10:00 형식"
            re_time = datas[0]
            datas.pop(datas.index(datas[0]))
            re_time = re_time.replace("%3A", ":", 2)
            if len(re_time.split(":")) == 2:
                re_time = re_time + ":00"
        else:
            time = parse.unquote(datas[0])
            if '시' or '분' in time:
                time = re.findall('\d+', time)  # 22시40분 => ['22','40]
                re_time = ':'.join(time)
                if len(time) == 2:
                    re_time = re_time + ":00"
                elif len(time) == 1:
                    re_time = re_time + ":00:00"


        return year, re_time, r_id

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
        user = self.get_user()
        exit_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        text = request.body.decode("utf-8").split('&')[8].split('=')[1]
        if not len(text) > 5 :
            self.slack_message('잘못된 입력입니다. "/사용법" 을 참고해주세요 :)')
            return Response(status=status.HTTP_204_NO_CONTENT)

        if len(text.split('+')) >= 3:
            #정정 입력 : 년월일, 시간, -breaking_time, id
            y, m, b_time, r_id = self.get_re_info(text)
            instance = self.get_queryset().filter(user=user, random_id=r_id).last()
            if not instance:
                # 해당 id 가 없는 경우
                self.slack_message('없는 ID 입니다.')
                return Response(status=status.HTTP_204_NO_CONTENT)
            if y is None:
                y = instance.entered_time.strftime('%Y-%m-%d')

            re_time = y + ' ' + m
            enter_time = instance.entered_time
            instance.is_user = True
            instance.exited_time = re_time
            instance.break_hours = b_time
            instance.total_hours = calculate_working_hours(enter_time, re_time, b_time)
            instance.save()
            username = get_real_name(user)
            self.slack_message('{}, 퇴근시각 변경되었습니다. --> `\033{}\033` 오늘도 수고하셨습니다 :)'.format(username, re_time))

        if len(text.split('+')) == 2:
            # 정상 입력 : -breaking_time, id
            b_time, r_id = self.get_info(text)
            instance = self.get_queryset().filter(user=user, random_id=r_id).last()
            if not instance:
                # 해당 id 가 없는 경우
                self.slack_message('없는 ID 입니다.')
                return Response(status=status.HTTP_204_NO_CONTENT)

            en_time = instance.entered_time
            instance.is_user = True
            instance.exited_time = exit_time
            instance.break_hours = b_time
            instance.total_hours = calculate_working_hours(en_time, exit_time, b_time)
            instance.save()
            username = get_real_name(user)
            self.slack_message('{}, 퇴근시각 {}  오늘도 수고하셨습니다 :)'.format(username, exit_time))

        return Response(status=status.HTTP_200_OK)

    def get_user(self):
        body = self.request.body.decode("utf-8")
        username = body.split('&')[6].split('=')[1]
        user = User.objects.filter(username=username).last()
        return user

    def get_info(self,text):
        datas = text.split('+')
        r_id = []
        for data in datas:
            if len(data) == 6:
                r_id = data
                datas.pop(datas.index(data))
        return datas[0], r_id

    def get_re_info(self, text):
        datas = text.split('+')
        year = []
        re_time = []
        r_id = []
        if '2022' in datas[0]:
            year = datas[0]
            datas = datas[1:]
        else:
            year = None

        for data in datas:
            if len(data) == 6:
                r_id = data
                datas.pop(datas.index(data))

        b_time = datas[-1]
        if '%3A' in datas[0]:  # "10:00:00 or 10:00 형식"
            re_time = datas[0]
            datas.pop(datas.index(datas[0]))
            re_time = re_time.replace("%3A", ":", 2)
            if len(re_time.split(":")) == 2:
                re_time = re_time + ":00"
        else:
            time = parse.unquote(datas[0])
            if '시' or '분' in time:
                time = re.findall('\d+', time)  #22시40분 => ['22','40]
                re_time = ':'.join(time)
                if len(time) == 2:
                    re_time = re_time + ":00"
                elif len(time) == 1:
                    re_time = re_time + ":00:00"

        return year, re_time, b_time, r_id

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
        post_data = {"text": '❗사용법! 띄어쓰기 주의❗\n 이번주 기록 확인 :"https://c1g8wf2m82.execute-api.ap-northeast-2.amazonaws.com/dev"\n',
                     "attachments": [{"text":
                                          "\n\n ⚙(시간)형식은 \n`\03310:00:00\033` or `\03321:00\033` or `\03310시30분\033` "
                                          "or `\03314시\033`"
                                          "\n"

                                          "\n\n\n🙋출근시 \n\n `\033/출근\033`   --> 오늘의 Id를 반환합니다. 반환된 Id로 정정시 사용합니다."

                                          "\n\n 🛠️`\033/출근 (시간) Id\033` : 출근 정정시   --> 순서 주의, Id 꼭 써주세요."
                                          "\n 🛠️`\033/출근 2022-01-31 (시간) Id\033` : 출근 날짜까지 정정시"
                                          "\n\n\n\n 🙆퇴근시 \n\n `\033/퇴근 -2 Id\033`   --> -2는 쉬었던 시간, 출근시 받았던 Id 꼭 써주세요."
                                          "\n\n 🛠️`\033/퇴근 (시간) -2 Id\033` : 퇴근 정정시  --> 순서주의, 쉬었던 시간, Id 꼭 써주세요"
                                          "\n 🛠️`\033/퇴근 2022-xx-xx (시간) -2 Id\033` : 퇴근 날짜까지 정정시   --> 순서주의, 쉬었던 시간, Id 꼭 써주세요"}]}

        data = json.dumps(post_data)
        headers = {'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8'}
        response = requests.post(incomming_url, headers=headers, data=data)
        return Response(status=status.HTTP_200_OK)


class WebHookCheckId(GenericAPIView):
    def post(self, request):
        user = self.get_user()
        username = get_real_name(user)
        last_id = user.logs.last().random_id
        incomming_url = load_credential("SLACK_INCOMMING_URL")
        post_data = {"text": '{} 오늘의 ID 입니다 --> {}'.format(username, last_id)}
        data = json.dumps(post_data)
        headers = {'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8'}
        response = requests.post(incomming_url, headers=headers, data=data)
        return Response(status=status.HTTP_200_OK)

    def get_user(self):
        body = self.request.body.decode("utf-8")
        username = body.split('&')[6].split('=')[1]
        user = User.objects.filter(username=username).last()
        return user


class ChartView(TemplateView):
    template_name = "home.html"

    def get_context_data(self):
        context = super().get_context_data()
        context['chart'] = self.working_chart()
        # context['title'] = self.weekly_slogan_title()
        # context['body'] = self.weekly_slogan_body()
        return context

    def working_chart(self):

        user_queryset = User.objects.filter(is_active=True)
        total_data = {}

        for obj in user_queryset:
            if WorkLogs.objects.filter(user=obj).exists():
                total_data[obj.korean_name] = get_week_data(WorkLogs.objects.filter(user=obj))

        # ordering
        ordered = OrderedDict(sorted(total_data.items(), key=lambda i: i[1]['total'], reverse=True))
        total_data = dict(ordered)

        return total_data

    def weekly_slogan_title(self):
        obj = Slogan.objects.filter(is_active=True).last()
        return obj.title

    def weekly_slogan_body(self):
        obj = Slogan.objects.filter(is_active=True).last()
        return obj.body
