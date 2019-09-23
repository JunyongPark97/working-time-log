from django.urls import path

from slack.views import WebHookEnter, WebHookExit, WebHookExplanation

urlpatterns = [
    path('enter/', WebHookEnter.as_view(), name='webhook-enter'),
    path('exit/', WebHookExit.as_view(), name='webhook-exit'),
    path('explain/', WebHookExplanation.as_view(), name='webhook-explane'),
]
