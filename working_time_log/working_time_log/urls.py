from django.conf.urls import url
from django.contrib import admin
from django.urls import path, include
from slack.views import ChartView

urlpatterns = [
    path('admin/', admin.site.urls),
    url(r'^webhook/', include('slack.urls')),
    path('', ChartView.as_view()),
]
