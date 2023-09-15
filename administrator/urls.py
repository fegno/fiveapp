from django.conf.urls import include
from administrator import api
from django.urls import path



urlpatterns = [
    path('module-list/', api.ModuleDetailsList.as_view(), name='module-details-list'),
]