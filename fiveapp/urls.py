from django.contrib import admin
from django.conf.urls import include, url
from django.conf import settings
from django.views.static import serve
from django.urls import path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include(("fiveapp.api_urls", "project"), namespace="api")),

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
