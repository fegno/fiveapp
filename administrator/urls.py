from django.conf.urls import include
from administrator import api
from django.urls import path, re_path

urlpatterns = [
    re_path(r'^home-page/', api.Homepage.as_view(), name='home-page'),
    re_path(r'^list-subscription-plans/', api.ListSubscriptionPlans.as_view(), name='list-subscription-plans'),
    re_path(r'^view-bundle-details/(?P<pk>\d+)/$', api.ViewBundle.as_view()),
    re_path(r'^list-modules/', api.ListModules.as_view(), name='list-modules'),
    re_path(r'^select-free-subscription/', api.SelectFreeSubscription.as_view(), name='select-free-subscription'),

    re_path(r'^module/<int:pk>/users/', api.UserInModule.as_view(), name='users-under-the-module')

]