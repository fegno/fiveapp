from django.contrib import admin
from django.conf.urls import include, url
from django.conf import settings
from django.views.static import serve

urlpatterns = [
    url(r"^admin/", admin.site.urls),
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
