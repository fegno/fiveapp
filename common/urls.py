from django.conf.urls import url
from common import views

urlpatterns = [
    url(r"^$", views.Login.as_view(), name="home")
]