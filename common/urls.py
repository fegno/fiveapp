from django.conf.urls import url
from common import views

urlpatterns = [
    url(r"^$", views.Login.as_view(), name="home"),

    url(r'^accept-reject/(?P<user_invite_id>\d+)/$', views.AcceptReject.as_view(), name='accept-reject'),


    # re_path(r'^link-verification/(?P<user_invite_id>\d+)/$', api.InviteLinkVerification.as_view(), name='link-verification'),
    # re_path(r'^accept-reject/(?P<user_invite_id>\d+)/$', api.AcceptReject.as_view(), name='accept-reject'),
]