from django.conf.urls import include
from administrator import api
from django.urls import path



urlpatterns = [
    path('home-page/', api.Homepage.as_view(), name='home-page'),
]