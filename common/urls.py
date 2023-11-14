from django.conf.urls import url
from common import views

urlpatterns = [
    url(r"^$", views.Login.as_view(), name="home"),

    url(r'^accept-reject/(?P<user_invite_id>\d+)/$', views.AcceptReject.as_view(), name='accept-reject'),

]