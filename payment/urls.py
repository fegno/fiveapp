from django.conf.urls import include
from payment import api
from django.urls import path, re_path

urlpatterns = [
    re_path(r'^initiate-payment/', api.InitiatePayment.as_view(), name='initiate-payment'),
]