from django.shortcuts import render, redirect
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db import transaction
from django.http import JsonResponse, HttpResponse

from django.shortcuts import get_object_or_404
from django.views import View
from django.views.generic.base import TemplateView
from django.contrib import messages
from fiveapp.utils import get_error, utc_now
from django.views import View
from user.permissions import (
    IsSuperAdminMixin,
)

from datetime import timedelta, date, datetime
from django.db.models import (
    Prefetch,
    Count,
    Case,
    When,
    Value,
    F,
    Q,
    BooleanField,
    CharField,
)
from django.http import HttpResponse
import json


class LandingPage(IsSuperAdminMixin, TemplateView):
    template_name = "admin/home/home.html"

    def get(self, request):
        context = {}
       
        context = {
            "user": request.session["user"],
        }
        return render(request, self.template_name, context)