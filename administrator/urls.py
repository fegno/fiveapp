from django.conf.urls import include
from administrator import api
from django.urls import path

urlpatterns = [
    path('home-page/', api.Homepage.as_view(), name='home-page'),
    path('list-subscription-plans/', api.ListSubscriptionPlans.as_view(), name='list-subscription-plans'),
    path('view-bundle-details/(?P<pk>\d+)/', api.ViewBundle.as_view()),

]