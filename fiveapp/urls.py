from django.contrib import admin
from django.conf.urls import include, url
from django.conf import settings
from django.views.static import serve
from django.urls import path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include(("fiveapp.api_urls", "project"), namespace="api")),
    path("", include(("common.urls", "common"), namespace="common")),
    path(
        "superadmin/",
        include(("superadmin.urls", "superadmin"), namespace="superadmin"),
    ),
    path(
        "administrator/", include(("administrator.urls", "administrator"), namespace="administrator")
    )

]

if settings.DEBUG:
    urlpatterns += [
        url(
            r"^media/(?P<path>.*)$",
            serve,
            {
                "document_root": settings.MEDIA_ROOT,
            },
        ),
    ]
