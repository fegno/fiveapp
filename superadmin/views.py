from django.shortcuts import render, redirect
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db import transaction
from django.http import JsonResponse, HttpResponse
from django.utils import timezone

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
from superadmin.models import ModuleDetails, FeatureDetails,  BundleDetails, ModuleReports
from user.models import UserProfile
from superadmin.forms import ModuleForm, BundleForm
from administrator.models import PurchaseDetails, SubscriptionDetails, CustomRequest
from payment.models import PaymentAttempt

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
                if request.POST.getlist("report_type"):
                    for i in request.POST.getlist("report_type"):
                        ModuleReports.objects.create(
                            module=module,
                            report=i
                        )
                messages.success(request, "Added successfully")
        else:
            response_dict["reason"] = get_error(form)
            messages.error(request, response_dict["reason"])
        return redirect(request.GET.get("return") or "superadmin:landing-page")


class EditModule(IsSuperAdminMixin, TemplateView):
    template_name = "admin/home/edit_module.html"

    def get(self, request, pk):
        context = {}
        module = ModuleDetails.objects.filter(
            is_active=True, id=pk
        ).last()
        reports = list(ModuleReports.objects.filter(
            module=module
        ).values_list("report", flat=True))

        features = FeatureDetails.objects.filter(
            modules=module,
            is_active=True
        )
        context = {
            "user": request.session["user"],
            "module":module,
            "reports":reports,
            "features":features
        }
        return render(request, self.template_name, context)

    def post(self, request, pk):
        response_dict = {}
        module = ModuleDetails.objects.filter(
            is_active=True, id=pk
        ).last()
        form = ModuleForm(request.POST, request.FILES, instance=module)
        if not request.FILES.get("csv_file"):
            del form.fields["csv_file"]
        
        feature_list = request.POST.getlist("feature")
        benifit_list = request.POST.getlist("benifit")
        pr_file = []
        if form.is_valid():
            with transaction.atomic():
                module = form.save()
                to_save = []

                FeatureDetails.objects.filter(modules=module,).delete()
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

                ModuleReports.objects.filter(module=module,).delete()
                if request.POST.getlist("report_type"):
                    for i in request.POST.getlist("report_type"):
                        ModuleReports.objects.create(
                            module=module,
                            report=i
                        )
                messages.success(request, "Added successfully")
        else:
            response_dict["reason"] = get_error(form)
            messages.error(request, response_dict["reason"])
        return redirect(request.GET.get("return") or "superadmin:landing-page")

class ListBundle(IsSuperAdminMixin, TemplateView):
    template_name = "admin/bundle/bundle.html"

    def get(self, request):
        context = {}
        all_modules = ModuleDetails.objects.filter(
            is_active=True,
            is_submodule=False
        )
        bundle = BundleDetails.objects.filter(
            is_active=True,
        )
        context = {
            "user": request.session["user"],
            "bundle":bundle,
            "all_modules":all_modules
        }
        return render(request, self.template_name, context)

    def post(self, request):
        response_dict = {}
        form = BundleForm(request.POST, request.FILES)
        if form.is_valid():
            with transaction.atomic():
                bundle = form.save()   
                if request.POST.getlist("modules"):
                    bundle.modules.add(*request.POST.getlist("modules"))             
                messages.success(request, "Added successfully")
        else:
            response_dict["reason"] = get_error(form)
            messages.error(request, response_dict["reason"])
        return redirect(request.GET.get("return") or "superadmin:list-bundle")

class ListAdmin(IsSuperAdminMixin, TemplateView):
    template_name = "admin/admin/admin.html"

    def get(self, request):
        context = {}
        all_admins = UserProfile.objects.filter(
            is_active=True,
            user_type="ADMIN"
        )
        context = {
            "user": request.session["user"],
            "all_admins":all_admins,
        }
        return render(request, self.template_name, context)

class ListUsers(IsSuperAdminMixin, TemplateView):
    template_name = "admin/users/users.html"

    def get(self, request):
        context = {}
        users = UserProfile.objects.filter(
            is_active=True,
            user_type="USER"
        )
        context = {
            "user": request.session["user"],
            "users":users,
        }
        return render(request, self.template_name, context)


class ListCustomRequest(IsSuperAdminMixin, TemplateView):
    template_name = "admin/request/request.html"

    def get(self, request):
        context = {}
        custom = CustomRequest.objects.filter(
            is_active=True,
        ).order_by("-id")
      
        context = {
            "user": request.session["user"],
            "custom":custom,
        }
        return render(request, self.template_name, context)

class EditRequest(IsSuperAdminMixin, TemplateView):
    template_name = "admin/request/edit_request.html"

    def get(self, request, pk):
        context = {}
        custom = CustomRequest.objects.filter(
            is_active=True, id=pk
        ).last()
        custom_modules = list(custom.module.all().values_list("id", flat=True))
        custom_bundle = list(custom.bundle.all().values_list("id", flat=True))
        modules = ModuleDetails.objects.filter(
            is_active=True,
        )
        bundle = BundleDetails.objects.filter(
            is_active=True,
        )
        context = {
            "custom":custom,
            "modules":modules,
            "bundle":bundle,
            "custom_modules":custom_modules
        }
        return render(request, self.template_name, context)

    def post(self,request, pk):
        response_dict={'status':False}
        bundle_ids = request.POST.getlist("bundle")
        modules_ids = request.POST.getlist("modules")
        total_price = request.POST.get("total_price")
        subscription_type = request.POST.get("subscription_type")
        payment_intent_id = request.POST.get("payment_intent_id")

        custom = CustomRequest.objects.filter(
            is_active=True, id=pk
        ).last()
    
        order = PurchaseDetails.objects.create(
            user=custom.user,
            status="Placed",
            subscription_type=subscription_type,
            total_price=total_price,
            is_subscribed=True,
            custom_request=pk
        )
        if modules_ids:
            order.module.add(*modules_ids)    
        if bundle_ids:  
            order.bundle.add(*bundle_ids)  

        PaymentAttempt.objects.create(
            parchase_user_type="Subscription",
            parchase=order,user=custom.user,
            currency='gbp',
            amount=order.total_price,
			status='succeeded',
            last_attempt_date=timezone.now(),
            payment_intent_id=payment_intent_id
        )
        if modules_ids:
            for module_id in modules_ids:
                order.module.add(module_id)
        if bundle_ids:
            for bundle_id in bundle_ids:
                order.bundle.add(bundle_id)
        subscription = SubscriptionDetails.objects.filter(
            user=order.user, 
            is_subscribed=True
        ).last()
        if subscription_type == "WEEK":
            order.subscription_start_date =  timezone.now().date()
            if subscription:
                end_date = subscription.subscription_end_date
            else:
                end_date = timezone.now().date()  + timedelta(days=7)
            order.subscription_end_date =  end_date
        elif  subscription_type == "MONTH":
            order.subscription_start_date =  timezone.now().date()
            if subscription:
                end_date = subscription.subscription_end_date
            else:
                end_date = timezone.now().date()  + timedelta(days=30)
            order.subscription_end_date =  end_date
        elif subscription_type == "YEAR":
            order.subscription_start_date =  timezone.now().date() 
            if subscription:
                end_date = subscription.subscription_end_date
            else:  
                end_date = timezone.now().date()  + timedelta(days=365)
            order.subscription_end_date =  end_date
        order.save()


        custom.status  = "Placed"
        custom.total_price = total_price
        custom.subscription_type = subscription_type
        custom.subscription_end_date = order.subscription_end_date
        custom.subscription_start_date = order.subscription_start_date
        custom.save()

        if subscription:
            if subscription.subscription_end_date < timezone.now().date():
                subscription.subscription_start_date = order.subscription_start_date
                subscription.subscription_end_date = order.subscription_end_date
                subscription.is_subscribed = True
                subscription.module.clear()
                subscription.bundle.clear()
                if order.module:
                    subscription.module.add(list(order.module.values_list("id", flat=True)))      
                if order.bundle:
                    subscription.bundle.add(list(order.bundle.values_list("id", flat=True)))    
            else:
                if modules_ids:
                    subscription.module.add(*modules_ids)    
                if bundle_ids:  
                    subscription.bundle.add(*bundle_ids)  
        else:
            subscription = SubscriptionDetails.objects.create(
                user=custom.user,
                subscription_start_date=timezone.now().date(),
                subscription_end_date=end_date,
                is_subscribed=True,
                subscription_type=subscription_type
            )
            if modules_ids:
                subscription.module.add(*modules_ids)    
            if bundle_ids:  
                subscription.bundle.add(*bundle_ids)  
        messages.success(request, "Updated successfully")
        return redirect("superadmin:list-custom-request")