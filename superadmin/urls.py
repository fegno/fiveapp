from django.conf.urls import include, url
from superadmin import views

urlpatterns = [
    url(r"^landing-page/$", views.LandingPage.as_view(), name="landing-page"),
    url(r"^list-bundle/$", views.ListBundle.as_view(), name="list-bundle"),
    url(r"^list-admin/$", views.ListAdmin.as_view(), name="list-admin"),
    url(r"^list-users/$", views.ListUsers.as_view(), name="list-users"),
    url(r"^edit-module/(?P<pk>\d+)/$", views.EditModule.as_view(), name="edit-module"),
]