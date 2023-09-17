from django.conf.urls import include
from administrator import api
from django.urls import path, re_path

urlpatterns = [
    re_path(r'^home-page/', api.Homepage.as_view(), name='home-page'),
    re_path(r'^list-subscription-plans/', api.ListSubscriptionPlans.as_view(), name='list-subscription-plans'),
    re_path(r'^view-bundle-details/(?P<pk>\d+)/$', api.ViewBundle.as_view()),
    re_path(r'^list-modules/', api.ListModules.as_view(), name='list-modules'),

]