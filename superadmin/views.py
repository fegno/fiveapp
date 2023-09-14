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
from superadmin.models import ModuleDetails, FeatureDetails
from superadmin.forms import ModuleForm

class LandingPage(IsSuperAdminMixin, TemplateView):
    template_name = "admin/home/home.html"

    def get(self, request):
        context = {}
        all_modules = ModuleDetails.objects.filter(
            is_active=True,
        )
        modules = ModuleDetails.objects.filter(
            is_active=True,
            is_submodule=False
        ).values("title", "id")
        context = {
            "user": request.session["user"],
            "modules":modules,
            "all_modules":all_modules
        }
        return render(request, self.template_name, context)

    def post(self, request):
        response_dict = {}
        form = ModuleForm(request.POST, request.FILES)
        feature_list = request.POST.getlist("feature")
        benifit_list = request.POST.getlist("benifit")
        pr_file = []
        if form.is_valid():
            with transaction.atomic():
                module = form.save()
                to_save = []
                if request.POST.get("feature"):
                    for i in range(0, len(feature_list)):
                        to_save.append(
                            FeatureDetails(
                                modules=module,
                                feature=feature_list[i],
                                benifit=benifit_list[i]
                            )
                        )
                    FeatureDetails.objects.bulk_create(to_save)
                messages.success(request, "Added successfully")
        else:
            response_dict["reason"] = get_error(form)
            messages.error(request, response_dict["reason"])
        return redirect(request.GET.get("return") or "superadmin:landing-page")