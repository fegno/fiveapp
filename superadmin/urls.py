from django.conf.urls import include, url
from superadmin import views

urlpatterns = [
    url(r"^landing-page/$", views.LandingPage.as_view(), name="landing-page"),
]