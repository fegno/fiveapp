from django.conf.urls import include
from django.urls import path

urlpatterns = [
    path("user/", include("user.urls")),
    path(
        "administrator/", include(("administrator.urls", "administrator"), namespace="administrator")
    ),
    path("payment/", include("payment.urls")),
]
