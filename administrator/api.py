import random
from django.shortcuts import render
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from payment.models import PaymentAttempt
from user.api_permissions import CustomTokenAuthentication, IsAdmin
from rest_framework.views import APIView
from rest_framework import status
from datetime import datetime
from django.utils import timezone
from datetime import timedelta, date, datetime
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import (
    Q,
    Sum,
    Count,
    Max,
    Prefetch,
    Case,
    When,
    Value,
    CharField,
    BooleanField,
    IntegerField,
    F,
    IntegerField,
    Avg,
    FloatField,
    Func,
    DecimalField,
    ExpressionWrapper,
    Subquery,
    OuterRef,
    Min,
    Max
)
from fiveapp.utils import PageSerializer, localtime

from administrator.models import PurchaseDetails, SubscriptionDetails,  CsvLogDetails, UploadedCsvFiles, AddToCart, CustomRequest, DepartmentWeightage, UserSubscriptionDetails
from administrator.serializers import (
    DeletedUserLogSerializers,
    InvitedUserSerializer,
    ModuleDetailsSerializer, 
    BundleDetailsSerializer,
    BundleDetailsLiteSerializer,
    ModuleSToUserserializer,
    PurchaseHistorySerializer,
    SubscriptionModuleSerilzer,
    SubscriptionPaymentAttemptsSerializer,
    UserAssignedModuleSerializers,
    CsvSerializers,
    UploadedCsvFilesSerializer,
    UserInviteSerializer,
    UserPaymentAttemptsSerializer,
    UserPurchaseHistorySerializer,
    SubscriptionParchaseSerializers,
    UserSubscriptionSerializers
)
from superadmin.models import (
    DeleteUsersLog,
    InviteDetails,
    ModuleDetails, 
    BundleDetails, 
    UserAssignedModules,
  
)
import csv

from user.models import LoginOTP, UserProfile
from django.db import transaction
from fiveapp.utils import get_error
from user.serializers import UserSerializer
from django.core.mail import send_mail, EmailMessage
from django.template.loader import render_to_string
from django.contrib.auth import get_user_model
from django.db.models.functions import Round
from dateutil.relativedelta import relativedelta 
from superadmin.models import FreeSubscriptionDetails


def random_otp_generator(size=4, chars="123456789"):
    return "".join(random.choice(chars) for _ in range(size))


class Homepage(APIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (CustomTokenAuthentication, IsAdmin)

    def get(self, request):
        response_dict = {"status": False}
        response_dict["take_subscription"] = False
        response_dict["free_subscription"] = False
        user = request.user
        response_dict["bundles"] = []
        response_dict["modules"] = []
        current_date = timezone.now().date()
        response_dict["total_modules"] = ModuleDetails.objects.filter(is_active=True, is_submodule=False).count()
        response_dict["total_bundles"] = BundleDetails.objects.filter(is_active=True).count()
        if user.user_type == "ADMIN":
            free_subscribed_modules = FreeSubscriptionDetails.objects.filter(
                user=request.user,
                free_subscription_end_date__gte=current_date
            )
            if free_subscribed_modules:
                response_dict["free_subscription"] = True
            expired_subscription = None
            subscription = SubscriptionDetails.objects.filter(
                user=request.user, 
                is_subscribed=True,
                subscription_end_date__gte=current_date
            ).order_by("-id").first()
            if not subscription:
                expired_subscription = SubscriptionDetails.objects.filter(
                    user=request.user
                ).order_by("-id").first()

            if subscription:
                free_subscribed_modules_ids = []
                free_subscribed_bundle_ids = []
                for i in free_subscribed_modules:
                    if i.module.all():
                        free_subscribed_modules_ids.extend(
                            list(i.module.all().values_list("id", flat=True))
                        )
                    if i.bundle.all():
                        free_subscribed_bundle_ids.extend(
                            list(i.bundle.all().values_list("id", flat=True))
                        )
                modules = ModuleDetails.objects.filter(is_active=True).filter(
                    Q(id__in=subscription.module.all().values_list("id", flat=True))|
                    Q(id__in=free_subscribed_modules_ids)
                ).order_by("module_identifier")
                bundles = BundleDetails.objects.filter(is_active=True).filter(
                    Q(id__in=subscription.bundle.all().values_list("id", flat=True))|
                    Q(id__in=free_subscribed_bundle_ids)
                )
                assigned_user = UserAssignedModules.objects.filter(
                    user__created_admin=request.user,
                ).filter(
                    Q(module__id__in=subscription.module.all().values_list("id", flat=True))|
                    Q(module__id__in=free_subscribed_modules_ids)
                ).values_list("user__id", flat=True)

                user_c  = UserProfile.objects.filter(id__in=assigned_user).count()
                response_dict["bundles"] = BundleDetailsSerializer(bundles,context={"request": request}, many=True).data
                response_dict["modules"] = ModuleDetailsSerializer(modules,context={"request": request}, many=True,).data
                response_dict["status"] = True
                response_dict["take_subscription"] = True
                response_dict["assigned_user"] = user_c
                response_dict["total_users"] = user.available_free_users + user.available_paid_users
                return Response(response_dict, status=status.HTTP_200_OK)
            elif expired_subscription:
                if expired_subscription:
                    free_subscribed_modules_ids = []
                    free_subscribed_bundle_ids = []
                    for i in free_subscribed_modules:
                        if i.module.all():
                            free_subscribed_modules_ids.extend(
                                list(i.module.all().values_list("id", flat=True))
                            )
                        if i.bundle.all():
                            free_subscribed_bundle_ids.extend(
                                list(i.bundle.all().values_list("id", flat=True))
                            )

                    modules = ModuleDetails.objects.filter(is_active=True).filter(
                        Q(id__in=free_subscribed_modules_ids)
                    ).order_by("module_identifier")
                    bundles = BundleDetails.objects.filter(is_active=True).filter(
                        Q(id__in=free_subscribed_bundle_ids)
                    )
                    response_dict["bundles"] = BundleDetailsSerializer(bundles,context={"request": request}, many=True).data
                    response_dict["modules"] = ModuleDetailsSerializer(modules,context={"request": request}, many=True,).data

                    exp_modules = ModuleDetails.objects.filter(is_active=True).filter(id__in=expired_subscription.module.all().values_list("id", flat=True)).order_by("module_identifier")
                    exp_bundles = BundleDetails.objects.filter(is_active=True, id__in=expired_subscription.bundle.all().values_list("id", flat=True))
                    response_dict["message"] = "Subscription Expired"
                    response_dict["expired_modules"] = ModuleDetailsSerializer(exp_modules, context={"request":request}, many=True).data
                    response_dict["expired_bundles"] = ModuleDetailsSerializer(exp_bundles, context={"request":request}, many=True).data
                    return Response(response_dict, status=status.HTTP_200_OK)
                else:
                    response_dict["error"] = "Not started your any subscription"
                    return Response(response_dict, status=status.HTTP_200_OK)
            elif free_subscribed_modules:
                response_dict["free_subscription"] = True
                free_subscribed_modules_ids = []
                free_subscribed_bundle_ids = []
                for i in free_subscribed_modules:
                    if i.module.all():
                        free_subscribed_modules_ids.extend(
                            list(i.module.all().values_list("id", flat=True))
                        )
                    if i.bundle.all():
                        free_subscribed_bundle_ids.extend(
                            list(i.bundle.all().values_list("id", flat=True))
                        )
                modules = ModuleDetails.objects.filter(is_active=True, id__in=free_subscribed_modules_ids).order_by("module_identifier")
                bundles = BundleDetails.objects.filter(is_active=True, id__in=free_subscribed_bundle_ids)
                assigned_user = UserAssignedModules.objects.filter(
                    user__created_admin=request.user,
                ).filter(
                    Q(module__id__in=modules.values_list("id", flat=True))|
                    Q(module__id__in=free_subscribed_modules_ids)
                ).values_list("user__id", flat=True)
                
                user_c  = UserProfile.objects.filter(id__in=assigned_user).count()
                response_dict["assigned_user"] = user_c
                response_dict["bundles"] = BundleDetailsSerializer(bundles,context={"request": request}, many=True).data
                response_dict["modules"] = ModuleDetailsSerializer(modules,context={"request": request}, many=True,).data
                response_dict["take_subscription"] = True
                response_dict["status"] = True
                return Response(response_dict, status=status.HTTP_200_OK)
            else:
                response_dict["error"] = "Not started your any subscription"
                return Response(response_dict, status=status.HTTP_200_OK)
        elif user.user_type == "USER":
            free_subscribed_modules = FreeSubscriptionDetails.objects.filter(
                user=request.user.created_admin,
                free_subscription_end_date__gte=current_date
            )
            free_subscribed_modules_ids = []
            for i in free_subscribed_modules:
                if i.module.all():
                    free_subscribed_modules_ids.extend(
                        list(i.module.all().values_list("id", flat=True))
                    )
            user_assigned_modules = UserAssignedModules.objects.filter(
                user=request.user
            ).last()
            modules_list = []
            if user_assigned_modules:
                modules_list = user_assigned_modules.module.all().values_list("id", flat=True)
            admin = user.created_admin
            expired_subscription = None
            subscription = SubscriptionDetails.objects.filter(
                user=admin, 
                is_subscribed=True,
                subscription_end_date__gte=current_date
            ).order_by("-id").first()
            if not subscription:
                expired_subscription = SubscriptionDetails.objects.filter(
                    user=admin
                ).order_by("-id").first()

            if subscription:
                modules = ModuleDetails.objects.filter(is_active=True, id__in=modules_list).filter(
                    Q(id__in=subscription.module.all().values_list("id", flat=True))|
                    Q(id__in=free_subscribed_modules_ids)
                ).order_by("module_identifier")
                response_dict["modules"] = ModuleDetailsSerializer(modules,context={"request": request}, many=True,).data
                response_dict["status"] = True
                response_dict["take_subscription"] = True
                return Response(response_dict, status=status.HTTP_200_OK)
            elif expired_subscription:
                modules = ModuleDetails.objects.filter(is_active=True, id__in=modules_list).filter(
                    Q(id__in=free_subscribed_modules_ids)
                ).order_by("module_identifier")
                response_dict["modules"] = ModuleDetailsSerializer(modules,context={"request": request}, many=True,).data
                response_dict["message"] = "Subscription Expired"
                response_dict["status"] = True
                response_dict["take_subscription"] = True
                return Response(response_dict, status=status.HTTP_200_OK)
            elif free_subscribed_modules:
                response_dict["free_subscription"] = True
                if free_subscribed_modules:
                    modules = ModuleDetails.objects.filter(is_active=True, id__in=modules_list).filter(
                        Q(id__in=free_subscribed_modules_ids)
                    ).order_by("module_identifier")
                    response_dict["modules"] = ModuleDetailsSerializer(modules,context={"request": request}, many=True,).data
                else:
                    response_dict["message"] = "Free Subscription Expired"
                response_dict["take_subscription"] = True
                response_dict["status"] = True
                return Response(response_dict, status=status.HTTP_200_OK)
            else:
                response_dict["error"] = "Not started your any subscription"
                return Response(response_dict, status=status.HTTP_200_OK)

        else:
            response_dict["error"] = "Access denied, Only Admin can access the module list"
            return Response(response_dict, status=status.HTTP_403_FORBIDDEN)
        

class ListSubscriptionPlans(APIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (CustomTokenAuthentication, IsAdmin)

    def get(self, request):
        response_dict = {"status": False}
        current_date = timezone.now().date()
        modules = ModuleDetails.objects.filter(is_active=True, is_submodule=False)
        bundles = BundleDetails.objects.filter(is_active=True)
        subscription = SubscriptionDetails.objects.filter(
            user=request.user, is_subscribed=True,
            subscription_end_date__gte=current_date
        ).last()
        if subscription:
            parent_mod = ModuleDetails.objects.filter(is_submodule=True).filter(
                id__in=subscription.module.all().values_list("id", flat=True)
            ).values_list("modules__id", flat=True)
            bundles = bundles.exclude(id__in=subscription.bundle.all().values_list("id", flat=True))
            modules = modules.filter(is_submodule=False).exclude(id__in=parent_mod).exclude(
                id__in=subscription.module.all().values_list("id", flat=True)
            )

        response_dict["bundles"] = BundleDetailsSerializer(bundles,context={"request": request}, many=True).data
        response_dict["modules"] = ModuleDetailsSerializer(modules,context={"request": request}, many=True,).data
        response_dict["status"] = True
        return Response(response_dict, status=status.HTTP_200_OK)

class ViewBundle(APIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (CustomTokenAuthentication, IsAdmin)

    def get(self, request, pk):
        response_dict = {"status": False}
        current_date = timezone.now().date()
        bundles = BundleDetails.objects.filter(
            is_active=True, id=pk).last()
        response_dict["bundles"] = BundleDetailsLiteSerializer(
            bundles,context={"request": request}).data
        response_dict["status"] = True
        return Response(response_dict, status=status.HTTP_200_OK)



class ListBundleModules(APIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (CustomTokenAuthentication, IsAdmin)

    def get(self, request, pk):
        response_dict = {"status": False}
        response_dict["modules"] = []
        current_date = timezone.now().date()
        bundle_mod = []
        
        subscribed_modules = []
        
        bundle_modules = BundleDetails.objects.filter(
            id=pk
        ).last()
        free_subscribed_modules = FreeSubscriptionDetails.objects.filter(
            user=request.user,
            free_subscription_end_date__gte=current_date
        )

        if bundle_modules:
            bundle_mod = bundle_modules.modules.all().values_list("id", flat=True)
        modules = ModuleDetails.objects.filter(is_active=True, id__in=bundle_mod).order_by("module_identifier")
        if request.user.user_type == "ADMIN":
            subscription = SubscriptionDetails.objects.filter(
                user=request.user, 
                is_subscribed=True,
                subscription_end_date__gte=current_date
            ).last()
            if subscription:
                subscribed_modules = modules.filter(
                    id__in=subscription.module.all().values_list("id", flat=True)
                )            
                response_dict["modules"] = ModuleDetailsSerializer(
                    subscribed_modules,context={"request": request, "from_module":True, 'admin':request.user}, many=True,).data
        else:
            user_assigned_modules = UserAssignedModules.objects.filter(
                user=request.user
            ).last()
            subscription = SubscriptionDetails.objects.filter(
                user=request.user.created_admin, 
                is_subscribed=True,
                subscription_end_date__gte=current_date
            ).last()
            free_subscribed_modules_ids = []
            for i in free_subscribed_modules:
                if i.module.all():
                    free_subscribed_modules_ids.extend(
                        list(i.module.all().values_list("id", flat=True))
                    )
            if user_assigned_modules and subscription:
                subscribed_modules = modules.filter(
                    Q(id__in=subscription.module.all().values_list("id", flat=True))|
                    Q(id__in=free_subscribed_modules_ids)
                ).filter(id__in=user_assigned_modules.module.all().values_list("id", flat=True))            
                response_dict["modules"] = ModuleDetailsSerializer(
                    subscribed_modules,context={"request": request, "from_module":True, 'admin':request.user.created_admin}, many=True,).data
            elif free_subscribed_modules:
                subscribed_modules = modules.filter(
                    Q(id__in=free_subscribed_modules_ids)
                ).filter(id__in=user_assigned_modules.module.all().values_list("id", flat=True))            
                response_dict["modules"] = ModuleDetailsSerializer(
                    subscribed_modules,context={"request": request, "from_module":True, 'admin':request.user.created_admin}, many=True,).data
                
        response_dict["status"] = True
        return Response(response_dict, status=status.HTTP_200_OK)



class ListParchasedModules(APIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (CustomTokenAuthentication, IsAdmin)

    def get(self, request):
        response_dict = {"status": False}
        response_dict["modules"] = []
        current_date = timezone.now().date()
        modules = ModuleDetails.objects.filter(is_active=True).order_by("module_identifier")
        subscribed_modules = []
        
        if request.user.user_type == "ADMIN":
            subscription = SubscriptionDetails.objects.filter(
                user=request.user, 
                is_subscribed=True,
                subscription_end_date__gte=current_date
            ).last()
            if subscription:
                subscribed_modules = modules.filter(
                    id__in=subscription.module.all().values_list("id", flat=True)
                )            
                response_dict["modules"] = ModuleDetailsSerializer(
                    subscribed_modules,context={"request": request, "from_module":True, "admin":request.user}, many=True,).data
        else:
            user_assigned_modules = UserAssignedModules.objects.filter(
                user=request.user
            ).last()
            subscription = SubscriptionDetails.objects.filter(
                user=request.user.created_admin, 
                is_subscribed=True,
                subscription_end_date__gte=current_date
            ).last()
            if user_assigned_modules and subscription:
                subscribed_modules = modules.filter(
                    id__in=subscription.module.all().values_list("id", flat=True)
                ).filter(id__in=user_assigned_modules.module.all().values_list("id", flat=True))            
                response_dict["modules"] = ModuleDetailsSerializer(
                    subscribed_modules,context={"request": request, "from_module":True, "admin":request.user.created_admin}, many=True,).data
        
        
        response_dict["status"] = True
        return Response(response_dict, status=status.HTTP_200_OK)

class ListModules(APIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (CustomTokenAuthentication, IsAdmin)

    def get(self, request):
        response_dict = {"status": False}
        current_date = timezone.now().date()

        
        free_subscribed_modules = FreeSubscriptionDetails.objects.filter(user=request.user, free_subscription_end_date__gte=current_date)
        expired_subscription = None
        all_modules = ModuleDetails.objects.filter(is_active=True).order_by("module_identifier")

        subscription = SubscriptionDetails.objects.filter(
            user=request.user, 
            is_subscribed=True,
            subscription_end_date__gte=current_date
        ).order_by("id").last()
 
        if not subscription:
            expired_subscription = SubscriptionDetails.objects.filter(
                user=request.user
            ).order_by("-id").first()

        free_subscribed_modules_ids = []
        for i in free_subscribed_modules:
            if i.module.all():
                free_subscribed_modules_ids.extend(
                    list(i.module.all().values_list("id", flat=True))
                )
                
        response_dict["unsubscribed_modules"] = []
        response_dict["subscribed_modules"] = []
        if subscription:
            modules = ModuleDetails.objects.filter(is_active=True).filter(
                Q(id__in=subscription.module.all().values_list("id", flat=True))|
                Q(id__in=free_subscribed_modules_ids)
            ).order_by("module_identifier")
            parent_mod = ModuleDetails.objects.filter(is_submodule=True).filter(
                Q(id__in=subscription.module.all().values_list("id", flat=True))|
                Q(id__in=free_subscribed_modules_ids)
            ).values_list("modules__id", flat=True)

            unsubscribed_modules = all_modules.filter(is_submodule=False).exclude(
                Q(id__in=modules) |
                Q(id__in=free_subscribed_modules_ids)
            ).exclude(id__in=parent_mod).order_by("module_identifier")
            response_dict["unsubscribed_modules"] = ModuleDetailsSerializer(unsubscribed_modules,context={"request": request}, many=True,).data
            response_dict["subscribed_modules"] = ModuleDetailsSerializer(
                modules,context={"request": request, "from_module":True, "admin":request.user}, many=True,).data
        if not subscription and free_subscribed_modules:
            modules = ModuleDetails.objects.filter(is_active=True).filter(
                Q(id__in=free_subscribed_modules_ids)
            ).order_by("module_identifier")

            parent_mod = ModuleDetails.objects.filter(is_submodule=True).filter(
                Q(id__in=free_subscribed_modules_ids)
            ).values_list("modules__id", flat=True)

            unsubscribed_modules = all_modules.filter(is_submodule=False).exclude(
                id__in=free_subscribed_modules_ids
            ).exclude(id__in=parent_mod).order_by("module_identifier")
            response_dict["subscribed_modules"] = ModuleDetailsSerializer(
                modules,context={"request": request, "from_module":True, "admin":request.user}, many=True,).data
            response_dict["unsubscribed_modules"] = ModuleDetailsSerializer(unsubscribed_modules,context={"request": request}, many=True,).data
        
        if not subscription and not free_subscribed_modules:
            all_modules = all_modules.filter(is_submodule=False)
            response_dict["unsubscribed_modules"] = ModuleDetailsSerializer(all_modules,context={"request": request}, many=True,).data
            
        
        response_dict["status"] = True
        return Response(response_dict, status=status.HTTP_200_OK)

class SelectFreeSubscription(APIView):

    permission_classes = (IsAuthenticated,)
    authentication_classes = (CustomTokenAuthentication, IsAdmin)

    def post(self, request):
        response_dict = {"status": False}
        bundle_ids = request.data.get("bundle_ids", [])
        modules_ids = request.data.get("modules_ids", [])
        if FreeSubscriptionDetails.objects.filter(
            user=request.user,
        ).filter(Q(module__id__in=modules_ids,) |Q(bundle__id__in=bundle_ids)):
            response_dict["error"]  = "Some of the module or bundle already free subscribed"
            return Response(response_dict, status=status.HTTP_400_BAD_REQUEST)
        user = request.user
        user.free_subscribed = True
        user.free_subscription_start_date = timezone.now().date()
        user.free_subscription_end_date = timezone.now().date()  + timedelta(days=15)
        user.save()
        free = FreeSubscriptionDetails.objects.create(
            user=user,
            free_subscription_start_date=timezone.now().date(),
            free_subscription_end_date = timezone.now().date()  + timedelta(days=15)
        )
        free.module.add(*modules_ids)   
        free.bundle.add(*bundle_ids)   
        free.save()

        response_dict["message"] = "success"
        response_dict["status"] = True
        return Response(response_dict, status.HTTP_200_OK)


class UserInModule(APIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (CustomTokenAuthentication,)

    def get(self, request, pk):
        response_dict = {"status": False}
        # Get the ModuleDetails instance
        try:
            module = ModuleDetails.objects.get(pk=pk)
        except ModuleDetails.DoesNotExist:
            return Response(
                {"error": "Module not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Filter users assigned to the module
        user_assigned = UserAssignedModules.objects.filter(
            module=module, user__created_admin=request.user
        )
        deleted_user = DeleteUsersLog.objects.filter(module=module,deleted_by=request.user)
        response_dict["users"] = UserAssignedModuleSerializers(user_assigned, context={"request": request}, many=True).data
        response_dict["deleted-users"] = DeletedUserLogSerializers(deleted_user, context={"request":request}, many=True).data
        response_dict["status"] = True
        return Response(response_dict, status=status.HTTP_200_OK)
    

class DeleteUserFromModule(APIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (CustomTokenAuthentication,)


    def post(self, request, module_id, pk):
        response_dict = {"status": False}

        try:
            user_to_delete = UserAssignedModules.objects.get(user__id=pk, user__created_admin=request.user)
            module_to_delete = ModuleDetails.objects.get(id=module_id)
            
            if not user_to_delete.module.filter(id=module_id).exists():
                response_dict["error"] = "User is not associated with the specified module"
                return Response(response_dict, status=status.HTTP_400_BAD_REQUEST)
            else:
                user_to_delete.module.remove(module_to_delete)
            
            # if DeleteUsersLog.objects.filter(user=user_to_delete.user, module=module_to_delete).exists():
            #     response_dict["error"] = "Already In deleted mode"
            #     return Response(response_dict, status=status.HTTP_400_BAD_REQUEST)

            # else:
            deleted_user = DeleteUsersLog(
                    deleted_by=request.user,
                    user=user_to_delete.user,
                )
            deleted_user.save()
            deleted_user.module.add(module_to_delete)
            response_dict["message"] = "Successfully deleted the user from the module"
            response_dict["status"] = True

            user_assigned = UserAssignedModules.objects.filter(
                module=module_to_delete, user__created_admin=request.user
            )
            deleted_users = DeleteUsersLog.objects.filter(module=module_to_delete, deleted_by=request.user)
            response_dict["users"] = UserAssignedModuleSerializers(user_assigned, context={"request": request}, many=True).data
            response_dict["deleted-users"] = DeletedUserLogSerializers(deleted_users, context={"request":request}, many=True).data
        
            return Response(response_dict, status=status.HTTP_200_OK)
        except UserAssignedModules.DoesNotExist:
            response_dict["error"] = "User not assigned with the ADMIN"
            return Response(response_dict, status=status.HTTP_404_NOT_FOUND)
    


class UploadCsv(APIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (CustomTokenAuthentication,)

    def post(self, request, pk):
        response_dict = {"status": False}
        csv_file = request.FILES.get("file")
        working_type = request.data.get("working_type")
        module = ModuleDetails.objects.filter(id=pk).last()
        if request.user.user_type == "ADMIN":
            current_date = timezone.now().date()
            subscription_ext = SubscriptionDetails.objects.filter(
                user=request.user, 
                is_subscribed=True,
                subscription_end_date__gte=current_date,
                module__id=pk
            ).order_by("-id").first()
            if not subscription_ext:
                if UploadedCsvFiles.objects.filter(
                    uploaded_by=request.user,
                    modules=module,
                ).count() > 5:
                    response_dict["error"] = "Module upload count exceed"
                    return Response(response_dict, status=status.HTTP_400_BAD_REQUEST)
        else:
            current_date = timezone.now().date()
            subscription_ext = SubscriptionDetails.objects.filter(
                user=request.user.created_admin, 
                is_subscribed=True,
                subscription_end_date__gte=current_date,
                module__id=pk
            ).order_by("-id").first()
            if not subscription_ext:
                if UploadedCsvFiles.objects.filter(
                    uploaded_by=request.user,
                    modules=module,
                ).count() > 5:
                    response_dict["error"] = "Module upload count exceed"
                    return Response(response_dict, status=status.HTTP_400_BAD_REQUEST)

        if not module:
            response_dict["error"] = "Module Not Found"
            return Response(response_dict, status=status.HTTP_400_BAD_REQUEST)
        if module.module_identifier != 9 and not csv_file:
            response_dict["error"] = "File Not Found"
            return Response(response_dict, status=status.HTTP_400_BAD_REQUEST)
        if module.module_identifier == 1 or  module.module_identifier == 2:
            if not working_type:
                response_dict["error"] = "Type Required"
                return Response(response_dict, status=status.HTTP_400_BAD_REQUEST)
        to_save = []
        if module.module_identifier != 9:
            decoded_file = csv_file.read().decode('utf-8').splitlines()
            reader = csv.DictReader(decoded_file)

        if module.module_identifier != 9:
            upload_log = UploadedCsvFiles.objects.create(
                uploaded_by=request.user,
                modules=module,
                csv_file=csv_file,
                working_type=working_type
            )
        else:
            workhouse_space = request.data.get("workhouse_space")
            total_orders_pay_day = request.data.get("total_orders_pay_day")
            operating_hours_day = request.data.get("operating_hours_day")
            actual_resource_per_day = request.data.get("actual_resource_per_day")
            actual_resource_per_hour = request.data.get("actual_resource_per_hour")
            cost_per_man = request.data.get("cost_per_man")
            temporary_man_cost = request.data.get("temporary_man_cost")
            temporary_man_arranged = request.data.get("temporary_man_arranged")
            productivity_varriation = request.data.get("productivity_varriation")
            lead_time = request.data.get("lead_time")
            resource_additional_cost = request.data.get("resource_additional_cost")
            shortage_of_manpower = request.data.get("shortage_of_manpower")
            order_loss = request.data.get("order_loss")
            cost_per_shipment = request.data.get("cost_per_shipment")
            delay_duration = request.data.get("delay_duration")
            sqft_allocation = request.data.get("sqft_allocation")

            upload_log = UploadedCsvFiles.objects.create(
                uploaded_by=request.user,
                modules=module,
                sqft_allocation=sqft_allocation,
                workhouse_space=workhouse_space,
                total_orders_pay_day=total_orders_pay_day,
                operating_hours_day=operating_hours_day,
                actual_resource_per_day=actual_resource_per_day,
                actual_resource_per_hour=actual_resource_per_hour,
                cost_per_man=cost_per_man,
                temporary_man_arranged=temporary_man_arranged,
                temporary_man_cost=temporary_man_cost,
                productivity_varriation=productivity_varriation,
                lead_time=lead_time,
                resource_additional_cost=resource_additional_cost,
                shortage_of_manpower=shortage_of_manpower,
                order_loss=order_loss,
                cost_per_shipment=cost_per_shipment,
                delay_duration=delay_duration,
            )
        if module.module_identifier == 1:
            for row in reader:
                if "S.NO"in row and "EMPLOYEE ID" in row and  "EMPLOYEE NAME"  in row and "TEAM" in row and "WORKING HOURS/WEEK/ MONTHLY":

                    to_save.append(
                        CsvLogDetails(
                            uploaded_file=upload_log,
                            sl_no=row.get("S.NO"),
                            employee_id=row.get("EMPLOYEE ID"),
                            employee_name=row.get("EMPLOYEE NAME"),
                            team=row.get("TEAM"),
                            working_hour=row.get("WORKING HOURS/WEEK/ MONTHLY")
                        )
                    )
                else:
                    upload_log.delete()
                    response_dict["error"] = "Field Mismatch"
                    return Response(response_dict, status=status.HTTP_400_BAD_REQUEST)
                    
        elif module.module_identifier == 2:
            for row in reader:
                to_save.append(
                    CsvLogDetails(
                        uploaded_file=upload_log,
                        sl_no=row.get("S.NO"),
                        employee_id=row.get("EMPLOYEE ID"),
                        employee_name=row.get("EMPLOYEE NAME"),
                        team=row.get("TEAM"),
                        designation=row.get("DESIGNATION"),
                        department=row.get("DEPARTMENTS"),
                        working_hour=row.get("WORKING HOUR")
                    )
                )

        elif module.module_identifier == 3:
            for row in reader:
                if "S.NO" in row and "EMPLOYEE ID" in row and  "EMPLOYEE NAME" in row and "DESIGNATION" in row and "DEPARTMENTS" in row and "WORKING HOURS/MONTHLY" in row:
                    to_save.append(
                        CsvLogDetails(
                            uploaded_file=upload_log,
                            sl_no=row.get("S.NO"),
                            employee_id=row.get("EMPLOYEE ID"),
                            employee_name=row.get("EMPLOYEE NAME"),
                            designation=row.get("DESIGNATION"),
                            department=row.get("DEPARTMENTS") if row.get("DEPARTMENTS") else row.get("DEPARTMENT"),
                            working_hour=row.get("WORKING HOURS/MONTHLY"),
                            hourly_rate=row.get("HOURLY RATE"),
                            total_pay=round(float(row.get("WORKING HOURS/MONTHLY", 0)) * float(row.get("HOURLY RATE", 0)), 2)

                        )
                    )
                else:
                    upload_log.delete()
                    response_dict["error"] = "Field Mismatch"
                    return Response(response_dict, status=status.HTTP_400_BAD_REQUEST)
        
        elif module.module_identifier == 4:
            for row in reader:
                if row.get("S.NO") and row.get("S.NO") != "":
                    individual_ach_in = 0
                    if row.get("INDIVIDUAL ACH. IN %") and "%" in row.get("INDIVIDUAL ACH. IN %"):
                        individual_ach_in = str(row.get("INDIVIDUAL ACH. IN %")).replace("%","")
                        individual_ach_in = float(individual_ach_in)
                    to_save.append(
                        CsvLogDetails(
                            uploaded_file=upload_log,
                            sl_no=row.get("S.NO"),
                            employee_id=row.get("EMPLOYEE ID"),
                            employee_name=row.get("EMPLOYEE NAME"),
                            designation=row.get("DESIGNATION"),
                            department=row.get("Department") if row.get("Department") else row.get("DEPARTMENT"),
                            working_hour=row.get("WORKING HOURS/MONTH", 0),
                            hourly_rate=row.get("HOURLY RATE"),
                            extra_hour = row.get("EXTRA WORKING HOURS", 0),
                            fixed_pay =row.get("FIXED PAY", 0),
                            individual_ach_in =individual_ach_in
                        )
                    )
        elif module.module_identifier == 5:
            for row in reader:
                gender = ""
                if row.get("Gender"):
                    gender = row.get("Gender").replace(" ","")
                to_save.append(
                    CsvLogDetails(
                        uploaded_file=upload_log,
                        sl_no=row.get("S.NO"),
                        employee_id=row.get("EMPLOYEE ID"),
                        employee_name=row.get("EMPLOYEE NAME"),
                        designation=row.get("DESIGNATION"),
                        department=row.get("department"),
                        working_hour=row.get("WORKING HOURS/ MONTH"),
                        age=row.get("AGE"),
                        fixed_pay =row.get("FIXED PAY", 0),
                        experience=row.get("experience"),
                        region=row.get("Region"),
                        gender=gender,

                    )
                )

        elif module.module_identifier == 6:
            c = 0
            for row in reader:
                c = c + 1
                to_save.append(
                    CsvLogDetails(
                        uploaded_file=upload_log,
                        sl_no=c,
                        department=row.get("DEPARTMENTS"),
                        system_name=row.get("SYSTEM NAME"),
                        factors_effected=row.get("FACTORS EFFECTED"),
                        downtime_week=row.get("DOWN TIME IN WEEK"),
                        impact_hour=row.get("IMPACT HOUR"),
                    )
                )

        elif module.module_identifier == 10:
            c = 0
            for row in reader:
                c = c + 1
                to_save.append(
                    CsvLogDetails(
                        uploaded_file=upload_log,
                        sl_no=c,
                        location=row.get("LOCATIONS"),
                        no_of_truck_required=row.get("No of truckers required"),
                        actual=row.get("Actual"),
                        vehicle_utilisation=row.get("Vehicle utilisation/ no of days running."),
                    )
                )

        elif module.module_identifier == 7:
            # call center
            c = 0
            for row in reader:
                employee_availability = 0
                calls_per_hour = 0
                conversion_rate = 0
                call_drop_rate = 0
                transaction_rate = 0
                if row.get("Employee Availability"):
                    employee_availability = str(row.get("Employee Availability").replace("%",""))
                if row.get("Calls per hour"):
                    calls_per_hour = row.get("Calls per hour")
                if row.get("conversion rate"):
                    conversion_rate = str(row.get("conversion rate").replace("%",""))
                if row.get("call drop rate"):
                    call_drop_rate = str(row.get("call drop rate").replace("%",""))
                if row.get("Transaction drop rates"):
                    transaction_rate = str(row.get("Transaction drop rates").replace("%",""))

                c = c + 1
                to_save.append(
                    CsvLogDetails(
                        uploaded_file=upload_log,
                        sl_no=c,
                        center_name=row.get("Center name"),
                        employee_name=row.get("Empoyee name"),
                        no_of_days_per_week=row.get("no of days per week ( 6days)"),
                        employee_availability=employee_availability,
                        calls_per_hour=calls_per_hour,
                        conversion_rate=conversion_rate,
                        call_drop_rate=call_drop_rate,
                        transaction_rate=transaction_rate,
                    )
                )

        elif module.module_identifier == 11:
            # support
            c = 0
            for row in reader:
                employee_availability = 0
                calls_per_hour = 0
                non_resloution = 0
                cx_call_no_response = 0
                transaction_rate = 0
                if row.get("Availability"):
                    employee_availability = str(row.get("Availability").replace("%",""))
                if row.get("Calls per hour"):
                    calls_per_hour = row.get("Calls per hour")
                if row.get("Non Resloution %"):
                    non_resloution = str(row.get("Non Resloution %").replace("%",""))
                if row.get("CX call no response"):
                    cx_call_no_response = str(row.get("CX call no response").replace("%",""))
                c = c + 1
                to_save.append(
                    CsvLogDetails(
                        uploaded_file=upload_log,
                        sl_no=c,
                        center_name=row.get("Center name"),
                        employee_name=row.get("Empoyee name"),
                        no_of_days_per_week=row.get("no of days per week ( 6days)"),
                        employee_availability=employee_availability,
                        calls_per_hour=calls_per_hour,
                        non_resloution=non_resloution,
                        cx_call_no_response=cx_call_no_response,
                    )
                )

        elif module.module_identifier == 12:
            # support
            c = 0
            for row in reader:
                employee_availability = 0
                calls_per_hour = 0
                non_resloution = 0
                cx_call_no_response = 0
                transaction_rate = 0
                if row.get("Availability"):
                    employee_availability = str(row.get("Availability").replace("%",""))
                if row.get("Calls per hour"):
                    calls_per_hour = row.get("Calls per hour")
                if row.get("conversion rate"):
                    conversion_rate = str(row.get("conversion rate").replace("%",""))
                if row.get("Impressions drop"):
                    impression_drop = str(row.get("Impressions drop").replace("%",""))
                c = c + 1
                to_save.append(
                    CsvLogDetails(
                        uploaded_file=upload_log,
                        sl_no=c,
                        center_name=row.get("Center name"),
                        employee_name=row.get("Empoyee name"),
                        no_of_days_per_week=row.get("no of days per week ( 6days)",0),
                        employee_availability=employee_availability,
                        total_impression_per_hour=row.get("Total impressions per hour", 0),
                        conversion_rate=conversion_rate,
                        impression_drop=impression_drop
                    )
                )

        elif module.module_identifier == 8:
            c = 0
            for row in reader:
                level_of_automation_possible = 0
                if row.get("level of automation possible in %"):
                    level_of_automation_possible = str(row.get("level of automation possible in %").replace("%",""))
                c = c + 1
                to_save.append(
                    CsvLogDetails(
                        uploaded_file=upload_log,
                        sl_no=c,
                        department=row.get("departments"),
                        no_of_man_hours_required=row.get("no. of Man hours required"),
                        no_of_resource_required=row.get("no. of resources required"),
                        software=row.get("software"),
                        software_cost=row.get("software cost"),
                        level_of_automation_possible=level_of_automation_possible
                    )
                )

        if module.module_identifier != 9:
            if (len(to_save)) < 1:
                upload_log.delete()
                response_dict["error"] = "CSV should contain atleast one entry"
                return Response(response_dict, status=status.HTTP_400_BAD_REQUEST)
            CsvLogDetails.objects.bulk_create(to_save)
      
        response_dict["csv_id"] = upload_log.id
        response_dict["message"] = "Successfully uploaded"
        response_dict["status"] = True
        return Response(response_dict, status=status.HTTP_200_OK)

class ListCsv(APIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (CustomTokenAuthentication,)

    def get(self, request, pk):
        response_dict = {"status": False}
        module = ModuleDetails.objects.filter(id=pk).last()
        if not module:
            response_dict["error"] = "Module Not Found"
            return Response(response_dict, status=status.HTTP_400_BAD_REQUEST)

        response_dict["module"] = {
            "id":module.id,
            "name":module.title,
            "department":module.department,
            "module_identifier":module.module_identifier
        }

        csv_log = UploadedCsvFiles.objects.filter(
            modules=module
        ).filter(
            Q(uploaded_by=request.user)|
            Q(uploaded_by__created_admin=request.user)
        ).order_by("-id")
        items_per_page = 100
        paginator = Paginator(csv_log, items_per_page)
        page = request.GET.get("page")
        try:
            items = paginator.page(page)
        except PageNotAnInteger:
            items = paginator.page(1)
        except EmptyPage:
            items = paginator.page(paginator.num_pages)
        serialized = UploadedCsvFilesSerializer(items, many=True, localize=True, context={"request":self.request}).data
        items.object_list = serialized
        response_dict["page"] = PageSerializer(items, serialize=False).data
        response_dict["status"] = True
        return Response(response_dict, status=status.HTTP_200_OK)


class ViewCsv(APIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (CustomTokenAuthentication,)

    def get(self, request, pk):
        response_dict = {}

        csv_file = UploadedCsvFiles.objects.filter(id=pk).first()

        if csv_file:
            csv_files = csv_file.csv_file
            decoded_file = csv_files.read().decode('utf-8')
            reader = csv.DictReader(decoded_file.splitlines())
            data_list = [reader.fieldnames]

            for row in reader:
                data_list.append(list(row.values()))
            response_dict["data"] = data_list
            
            return Response(response_dict, status=status.HTTP_200_OK)
        else:
            response_dict["error"] = "CSV file not found."
            return Response(response_dict, status=status.HTTP_400_BAD_REQUEST)

    


class GenerateReport(APIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (CustomTokenAuthentication,)

    def post(self, request, pk):
        response_dict = {"status": False}
        week_working_hour = request.data.get("week_working_hour", 0)

        monthly_revenue = request.data.get("monthly_revenue", 0)


        csv_file = UploadedCsvFiles.objects.filter(
            id=pk
        ).first()
        response_dict["module"] = {
            "id":csv_file.modules.id,
            "name":csv_file.modules.title,
            "department":csv_file.modules.department,
            "module_identifier":csv_file.modules.module_identifier
        }
        log  = CsvLogDetails.objects.filter(
            uploaded_file__id=pk
        ).filter(
            Q(uploaded_file__uploaded_by=request.user)|
            Q(uploaded_file__uploaded_by__created_admin=request.user)
        ).order_by("id")

        # if csv_file.is_report_generated:
        #     response_dict["error"] = "Report Already generated"
        #     return Response(response_dict, status=status.HTTP_200_OK)
        
        if csv_file.modules.module_identifier == 1 or csv_file.modules.module_identifier == 2:
            try:
                week_working_hour = float(week_working_hour) * 5.0
                if csv_file.working_type == "WEEK":
                    for i in log:
                        working_hr = float(i.working_hour)

                        
                        extra_hr = float(i.working_hour) - float(week_working_hour)
                        i.extra_hour = extra_hr
                        i.save()
                        if float(i.working_hour) < float(week_working_hour):
                            per_day = float(week_working_hour) / 5
                            abn = float(i.working_hour) / float(per_day)
                            absent = float(5.0) - float(abn)
                            i.absent_days = absent
                            i.save()
                            
                elif csv_file.working_type == "MONTH":
                    week_working_hour =float(week_working_hour) *4
                    for i in log:
                        working_hr = float(i.working_hour)
                    
                        extra_hr = float(i.working_hour) - float(week_working_hour)
                        i.extra_hour = extra_hr
                        i.save()
                        
                        if float(i.working_hour) < float(week_working_hour):
                            per_day = float(week_working_hour) / 20
                            abn = float(i.working_hour) / float(per_day)
                            absent = float(20.0) - float(abn)
                            i.absent_days = absent
                            i.save()

                csv_file.is_report_generated = True
                csv_file.standard_working_hour = week_working_hour
                csv_file.save()
                response_dict["status"] = True
                response_dict["message"] = "Generated"
            except Exception as e:
                response_dict["error"] = str(e)
        elif csv_file.modules.module_identifier == 3:
            try:
                departments = list(set(DepartmentWeightage.objects.filter(uploaded_file__id=pk).values_list("id", flat=True)))
                for i in departments:
                    dep_value = request.data.get(str(i), 0)
                    DepartmentWeightage.objects.filter(
                        id=i,
                    ).update(percentage=dep_value)
                csv_file.is_report_generated = True
                csv_file.monthly_revenue = monthly_revenue
                csv_file.save()
                response_dict["status"] = True
                response_dict["message"] = "Generated"
            except Exception as e:
                response_dict["error"] = str(e)

        elif csv_file.modules.module_identifier == 4:
            total_working_days = request.data.get("total_working_days", 0)
            total_working_hours = request.data.get("total_working_hours", 0)
            company_target_achieved = request.data.get("company_target_achieved", 0)
            department_target_achieved = request.data.get("department_target_achieved", 0)
            company_varriable_pay_wgt = request.data.get("company_varriable_pay_wgt", 0)
            department_varriable_pay_wgt = request.data.get("department_varriable_pay_wgt", 0)
            individual_varriable_pay_wgt = request.data.get("individual_varriable_pay_wgt", 0)
            try:
                for i in log:
                    i.overtime_pay = i.extra_hour * i.hourly_rate
                    i.no_of_holiday = (float(total_working_hours) - float(i.working_hour))/8
                    i.holiday_hours = float(i.working_hour) - float(total_working_hours)
                    i.holiday_pay = i.holiday_hours * i.hourly_rate
                    ind_cal = (i.fixed_pay * float(individual_varriable_pay_wgt))/100
                    i.individual_varriable_pay = (ind_cal * 0.5 * i.individual_ach_in)/100
                    i.department_varriable_pay = (ind_cal *0.5)*float(department_varriable_pay_wgt)/100
                    i.company_varriable_pay = (ind_cal * 0.5) * float(company_varriable_pay_wgt)/100
                    i.varriable_pay = (i.department_varriable_pay + i.individual_varriable_pay) + float(i.individual_ach_in)/100
                    i.gross_pay = i.varriable_pay + i.overtime_pay + i.fixed_pay + i.holiday_pay
                    i.save()

                csv_file.is_report_generated = True
                csv_file.total_working_days = total_working_days
                csv_file.total_working_hours = total_working_hours
                csv_file.company_target_achieved = company_target_achieved
                csv_file.department_target_achieved = department_target_achieved
                csv_file.company_varriable_pay_wgt = company_varriable_pay_wgt
                csv_file.department_varriable_pay_wgt = department_varriable_pay_wgt
                csv_file.individual_varriable_pay_wgt = individual_varriable_pay_wgt
                csv_file.save()
                response_dict["status"] = True
                response_dict["message"] = "Generated"
            except Exception as e:
                response_dict["error"] = str(e)
        elif csv_file.modules.module_identifier == 5:
            try:
                csv_file.is_report_generated = True
                csv_file.save()
                response_dict["status"] = True
                response_dict["message"] = "Generated"
            except Exception as e:
                response_dict["error"] = str(e)

        elif csv_file.modules.module_identifier == 6:
            try:
                peak_hour_sale_value = request.data.get("peak_hour_sale_value")
                non_peak_hour_sale_value = request.data.get("non_peak_hour_sale_value")
                sale_target = request.data.get("sale_target")
                peak_hour_sale_hr = request.data.get("peak_hour_sale_hr")
                non_peak_hour_sale_hr = request.data.get("non_peak_hour_sale_hr")
                employee_cost_target = request.data.get("employee_cost_target")
                csv_file.is_report_generated = True
                csv_file.peak_hour_sale_value = peak_hour_sale_value
                csv_file.non_peak_hour_sale_value = non_peak_hour_sale_value
                csv_file.sale_target = sale_target
                csv_file.peak_hour_sale_hr = peak_hour_sale_hr
                csv_file.non_peak_hour_sale_hr = non_peak_hour_sale_hr
                csv_file.employee_cost_target = employee_cost_target
                csv_file.save()
                response_dict["status"] = True
                response_dict["message"] = "Generated"
            except Exception as e:
                response_dict["error"] = str(e)

        elif csv_file.modules.module_identifier == 10:
            try:
                average_ton_per_truck = request.data.get("average_ton_per_truck")
                max_ton_per_truck = request.data.get("max_ton_per_truck")
                no_of_days = request.data.get("no_of_days")

                csv_file.is_report_generated = True
                csv_file.average_ton_per_truck = average_ton_per_truck
                csv_file.max_ton_per_truck = max_ton_per_truck
                csv_file.no_of_days = no_of_days

                csv_file.save()

                for i in log:
                    i.actual_calculated = i.actual * float(csv_file.average_ton_per_truck)
                    i.total_required_capacity = i.no_of_truck_required * float(csv_file.average_ton_per_truck)
                    per_ton_revenue_loss = (i.actual_calculated - i.total_required_capacity)*1000

                    i.per_ton_revenue_loss = float(csv_file.max_ton_per_truck) * float(per_ton_revenue_loss)
                    i.save()

                response_dict["status"] = True
                response_dict["message"] = "Generated"
            except Exception as e:
                response_dict["error"] = str(e)
        elif csv_file.modules.module_identifier == 9:
            try:
                csv_file.is_report_generated = True
                csv_file.save()
                response_dict["status"] = True
                response_dict["message"] = "Generated"
            except Exception as e:
                response_dict["error"] = str(e)

        elif csv_file.modules.module_identifier == 7:
            try:
                total_working_days = request.data.get("total_working_days")
                average_call_per_day = request.data.get("average_call_per_day")
                working_days = request.data.get("working_days")
                no_of_days_left = request.data.get("no_of_days_left")
                completed_days = request.data.get("completed_days")
                required_availability = request.data.get("required_availability")
                working_hour_per_day = request.data.get("working_hour_per_day")
                sales_target_in_terms = request.data.get("sales_target_in_terms")
                average_rate_per_sale = request.data.get("average_rate_per_sale")
                process = request.data.get("process")
                technology = request.data.get("technology")

                csv_file.is_report_generated = True
                csv_file.total_working_days = total_working_days
                csv_file.average_call_per_day = average_call_per_day
                csv_file.working_days = working_days
                csv_file.no_of_days_left = no_of_days_left
                csv_file.completed_days = completed_days
                csv_file.required_availability = required_availability
                csv_file.working_hour_per_day = working_hour_per_day
                csv_file.sales_target_in_terms = sales_target_in_terms
                csv_file.average_rate_per_sale = average_rate_per_sale
                csv_file.process = process
                csv_file.technology = technology
                csv_file.save()

                response_dict["status"] = True
                response_dict["message"] = "Generated"
            except Exception as e:
                response_dict["error"] = str(e)

        elif csv_file.modules.module_identifier == 11:
            try:
                call_handle_process = request.data.get("call_handle_process")
                technology = request.data.get("technology")
                average_call_per_day = request.data.get("average_call_per_day")
                employee_cost_target = request.data.get("employee_cost_target")
                working_days_per_week = request.data.get("working_days_per_week")
                average_cost_employee = request.data.get("average_cost_employee")
                working_days = request.data.get("working_days")
                completed_days = request.data.get("completed_days")
                working_hour_per_day = request.data.get("working_hour_per_day")
                average_cost_per_Call = request.data.get("average_cost_per_Call")
                required_availability = request.data.get("required_availability")

                csv_file.is_report_generated = True
                csv_file.call_handle_process = call_handle_process
                csv_file.technology = technology
                csv_file.average_call_per_day = average_call_per_day
                csv_file.employee_cost_target = employee_cost_target
                csv_file.average_cost_employee = average_cost_employee
                csv_file.working_days = working_days
                csv_file.working_days_per_week = working_days_per_week
                csv_file.completed_days = completed_days
                csv_file.working_hour_per_day = working_hour_per_day
                csv_file.average_cost_per_Call = average_cost_per_Call
                csv_file.required_availability = required_availability
                csv_file.save()
                response_dict["status"] = True
                response_dict["message"] = "Generated"
            except Exception as e:
                response_dict["error"] = str(e)

        elif csv_file.modules.module_identifier == 12:
            try:
                working_days_per_week = request.data.get("working_days_per_week")
                working_days = request.data.get("working_days")
                completed_days = request.data.get("completed_days")
                working_hour_per_day = request.data.get("working_hour_per_day")
                online_impression_target = request.data.get("online_impression_target")
                average_rate_per_impression = request.data.get("average_rate_per_impression")
                required_availability = request.data.get("required_availability")

                csv_file.is_report_generated = True
                csv_file.working_days_per_week = working_days_per_week
                csv_file.working_days = working_days
                csv_file.completed_days = completed_days
                csv_file.working_hour_per_day = working_hour_per_day
                csv_file.online_impression_target = online_impression_target
                csv_file.average_rate_per_impression = average_rate_per_impression
                csv_file.required_availability = required_availability
                csv_file.save()
                response_dict["status"] = True
                response_dict["message"] = "Generated"
            except Exception as e:
                response_dict["error"] = str(e)
        
        elif csv_file.modules.module_identifier == 8:
            try:
                average_pay_per_employee = request.data.get("average_pay_per_employee")
                automation_100 = request.data.get("automation_100")
                automation_75 = request.data.get("automation_75")
                automation_50 = request.data.get("automation_50")
                automation_30 = request.data.get("automation_30")

                csv_file.is_report_generated = True
                csv_file.average_pay_per_employee = average_pay_per_employee
                csv_file.automation_100 = automation_100
                csv_file.automation_75 = automation_75
                csv_file.automation_50 = automation_50
                csv_file.automation_30 = automation_30
                csv_file.save()
                response_dict["status"] = True
                response_dict["message"] = "Generated"
            except Exception as e:
                response_dict["error"] = str(e)
        else:
            response_dict["error"] = "Module not Valid"
        return Response(response_dict, status=status.HTTP_200_OK)
    

class ViewReport(APIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (CustomTokenAuthentication,)

    def get(self, request, pk):
        response_dict = {"status": False}
        csv_file = UploadedCsvFiles.objects.filter(
            id=pk
        ).first()
        if not csv_file.is_report_generated:
            response_dict["error"] = "Report not generated"
            return Response(response_dict, status=status.HTTP_200_OK)

        response_dict["module"] = {
            "id":csv_file.modules.id,
            "name":csv_file.modules.title,
            "department":csv_file.modules.department,
            "module_identifier":csv_file.modules.module_identifier
        }
        con_to_local = localtime(csv_file.created, request)
        response_dict["csv_file"] = {
            "name":csv_file.csv_file.name,
            "created":con_to_local.strftime("%d/%m/%Y %I:%M %p"),
            "uploaded_by":csv_file.uploaded_by.first_name,
        }
        status_list = [
            When(extra_hour__gt=0, then=Value("Overloaded")),
            When(extra_hour__lt=0, then=Value("Underloaded")),
            When(extra_hour=0, then=Value("Standard")),
        ]
        if csv_file.modules.module_identifier == 1:
            log  = tuple(CsvLogDetails.objects.filter(
                uploaded_file__id=pk,
                is_active=True
            ).filter(
                Q(uploaded_file__uploaded_by=request.user)|
                Q(uploaded_file__uploaded_by__created_admin=request.user)
            ).annotate(
                status=Case(
                    *status_list, default=Value(""), output_field=CharField()
                ),
            ).values(
                "team",
                "sl_no", "employee_id",
                "employee_name",
                "working_hour",
                "status",
                "absent_days"
            ).order_by("id"))
            response_dict["report"] = log
        elif csv_file.modules.module_identifier == 2:
            log  = tuple(CsvLogDetails.objects.filter(
                uploaded_file__id=pk,
                is_active=True
            ).filter(
                Q(uploaded_file__uploaded_by=request.user)|
                Q(uploaded_file__uploaded_by__created_admin=request.user)
            ).annotate(
                status=Case(
                    *status_list, default=Value(""), output_field=CharField()
                ),
            ).values(
                "team",
                "sl_no", 
                "employee_id",
                "employee_name",
                "working_hour",
                "status",
                "absent_days",
                "department",
                "designation",
                "extra_hour"
            ).order_by("id"))
            
            response_dict["report"] = log

        elif csv_file.modules.module_identifier == 3:
            log  = tuple(CsvLogDetails.objects.filter(
                uploaded_file__id=pk,
                is_active=True
            ).filter(
                Q(uploaded_file__uploaded_by=request.user)|
                Q(uploaded_file__uploaded_by__created_admin=request.user)
            ).values(
                "sl_no", 
                "employee_id",
                "employee_name",
                "department",
                "designation",
                "hourly_rate",
                "working_hour",
                "total_pay",
            ).order_by("id"))
            
            response_dict["report"] = log

        elif csv_file.modules.module_identifier == 4:
            log  = tuple(CsvLogDetails.objects.filter(
                uploaded_file__id=pk,
                is_active=True
            ).filter(
                Q(uploaded_file__uploaded_by=request.user)|
                Q(uploaded_file__uploaded_by__created_admin=request.user)
            ).values(
                "sl_no", 
                "employee_id",
                "employee_name",
                "department",
                "designation",
                "hourly_rate",
                "working_hour",
                "extra_hour",
                "gross_pay",
                "fixed_pay",
                "varriable_pay",
                "overtime_pay",
                "no_of_holiday",
                "holiday_hours",
                "holiday_pay",
                "individual_ach_in",
                "individual_varriable_pay",
                "department_varriable_pay",
                "company_varriable_pay"
            ).order_by("id"))
            
            response_dict["report"] = log

        elif csv_file.modules.module_identifier == 5:
            log  = tuple(CsvLogDetails.objects.filter(
                uploaded_file__id=pk,
                is_active=True
            ).filter(
                Q(uploaded_file__uploaded_by=request.user)|
                Q(uploaded_file__uploaded_by__created_admin=request.user)
            ).values(
                "sl_no", 
                "employee_id",
                "employee_name",
                "department",
                "designation",
                "fixed_pay",
                "age",
                "experience",
                "gender",
                "region"
            ).order_by("id"))
            
            response_dict["report"] = log

        elif csv_file.modules.module_identifier == 6:
            log  = tuple(CsvLogDetails.objects.filter(
                uploaded_file__id=pk,
                is_active=True
            ).filter(
                Q(uploaded_file__uploaded_by=request.user)|
                Q(uploaded_file__uploaded_by__created_admin=request.user)
            ).values(
                "sl_no", 
                "department",
                "system_name",
                "factors_effected",
                "downtime_week",
                "impact_hour",
            ).order_by("id"))
            response_dict["report"] = log
        
        elif csv_file.modules.module_identifier == 10:
            log  = tuple(CsvLogDetails.objects.filter(
                uploaded_file__id=pk,
                is_active=True
            ).filter(
                Q(uploaded_file__uploaded_by=request.user)|
                Q(uploaded_file__uploaded_by__created_admin=request.user)
            ).values(
                "sl_no", 
                "location",
                "no_of_truck_required",
                "actual",
                "vehicle_utilisation",
                "per_ton_revenue_loss",
                "total_required_capacity",
                "actual_calculated"
            ).order_by("id"))
            response_dict["report"] = log
        elif csv_file.modules.module_identifier == 7:
            log  = tuple(CsvLogDetails.objects.filter(
                uploaded_file__id=pk,
                is_active=True
            ).filter(
                Q(uploaded_file__uploaded_by=request.user)|
                Q(uploaded_file__uploaded_by__created_admin=request.user)
            ).values(
                "sl_no", 
                "employee_name",
                "center_name",
                "no_of_days_per_week",
                "employee_availability",
                "calls_per_hour",
                "conversion_rate",
                "call_drop_rate",
                "transaction_rate",
            ).order_by("id"))
            response_dict["report"] = log
        elif csv_file.modules.module_identifier == 8:
            log  = tuple(CsvLogDetails.objects.filter(
                uploaded_file__id=pk,
                is_active=True
            ).filter(
                Q(uploaded_file__uploaded_by=request.user)|
                Q(uploaded_file__uploaded_by__created_admin=request.user)
            ).values(
                "sl_no", 
                "department",
                "no_of_man_hours_required",
                "no_of_resource_required",
                "software",
                "software_cost",
                "level_of_automation_possible",
            ).order_by("id"))
            response_dict["report"] = log
        elif csv_file.modules.module_identifier == 11:
            log  = tuple(CsvLogDetails.objects.filter(
                uploaded_file__id=pk,
                is_active=True
            ).filter(
                Q(uploaded_file__uploaded_by=request.user)|
                Q(uploaded_file__uploaded_by__created_admin=request.user)
            ).values(
                "sl_no", 
                "employee_name",
                "center_name",
                "no_of_days_per_week",
                "employee_availability",
                "calls_per_hour",
                "cx_call_no_response",
                "non_resloution"
            ).order_by("id"))
            response_dict["report"] = log
        elif csv_file.modules.module_identifier == 12:
            log  = tuple(CsvLogDetails.objects.filter(
                uploaded_file__id=pk,
                is_active=True
            ).filter(
                Q(uploaded_file__uploaded_by=request.user)|
                Q(uploaded_file__uploaded_by__created_admin=request.user)
            ).values(
                "sl_no", 
                "employee_name",
                "center_name",
                "no_of_days_per_week",
                "employee_availability",
                "impression_drop",
                "total_impression_per_hour",
                "conversion_rate"
            ).order_by("id"))
            response_dict["report"] = log
        elif csv_file.modules.module_identifier == 9:
            minr2=60/5
            avg_order_per_hour = float(csv_file.total_orders_pay_day)/float(csv_file.operating_hours_day) if csv_file.operating_hours_day != 0 else 0
            total_productivity_at_warehouse = float(csv_file.total_orders_pay_day)*(365/7)
            csv_file_log = {
                "workhouse_space":csv_file.workhouse_space,
                "total_orders_pay_day":csv_file.total_orders_pay_day,
                "operating_hours_day":csv_file.operating_hours_day,
                "actual_resource_per_day":csv_file.actual_resource_per_day,
                "actual_resource_per_hour":csv_file.actual_resource_per_hour,
                "cost_per_man":csv_file.cost_per_man,
                "temporary_man_cost":csv_file.temporary_man_cost,
                "temporary_man_arranged":csv_file.temporary_man_arranged,
                "avg_order_per_hour":round(avg_order_per_hour),
                "no_resource_required_per_day":round(float(csv_file.total_orders_pay_day)*1.1/float(minr2)), 
                "no_resource_required_per_hour":round(avg_order_per_hour/float(minr2)), 
                "total_productivity_at_warehouse":round(total_productivity_at_warehouse),
                "inventory_turnover_rate":7,
                "total_resource_in_day":round(float(csv_file.actual_resource_per_day)+float(csv_file.temporary_man_arranged)),
                "manpower_as_per_standard":round(csv_file.workhouse_space/1500),
            }
            response_dict["report"] = csv_file_log
        response_dict["status"] = True
        return Response(response_dict, status=status.HTTP_200_OK)


class AnalyticsReport(APIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (CustomTokenAuthentication,)

    def get(self, request, pk):
        response_dict = {"status": False}
        csv_file = UploadedCsvFiles.objects.filter(
            id=pk
        ).first()
        if not csv_file.is_report_generated:
            response_dict["error"] = "Report not generated"
            return Response(response_dict, status=status.HTTP_200_OK)
        response_dict["module"] = {
            "id":csv_file.modules.id,
            "name":csv_file.modules.title,
            "department":csv_file.modules.department,
            "module_identifier":csv_file.modules.module_identifier
        }
        
        con_to_local = localtime(csv_file.created, request)
        response_dict["csv_file"] = {
            "name":csv_file.csv_file.name,
            "created":con_to_local.strftime("%d/%m/%Y %I:%M %p"),
            "uploaded_by":csv_file.uploaded_by.first_name,
        }

        status_list = [
            When(total_extra_hour__gt=0, then=Value("Overloaded")),
            When(total_extra_hour__lt=0, then=Value("Underloaded")),
            When(total_extra_hour=0, then=Value("Standard")),
        ]
        
        absent_status_list = [
            When(team_absent_days__gte=3, then=Value("Overloaded")),
            When(team_absent_days__gt=1,team_absent_days__lt=3 , then=Value("Underloaded")),
            When(team_absent_days__lte=1, then=Value("Standard")),

        ]
        

        if csv_file.modules.module_identifier == 1:
            standard_working_hour = csv_file.standard_working_hour
            if csv_file.working_type == "MONTH":
                standard_working_hour = standard_working_hour * 4
            log  = CsvLogDetails.objects.filter(
                uploaded_file__id=pk
            ).filter(
                Q(uploaded_file__uploaded_by=request.user)|
                Q(uploaded_file__uploaded_by__created_admin=request.user)
            ).values("team").annotate(
                employee_count=Count("id"),
                team_working_hr=Sum("working_hour"),
                team_absent_days=Sum("absent_days"),
                avg_team_working_hr=Avg("working_hour"),
                total_extra_hour=Sum("extra_hour")
            ).annotate(
                team_actual_working_hr=F("employee_count")*standard_working_hour
            ).annotate(
                status=Case(
                    *status_list, default=Value(""), output_field=CharField()
                ),
                absent_status=Case(
                    *absent_status_list, default=Value(""), output_field=CharField()
                ),
            ).values(
                "team", 
                "employee_count",
                "team_working_hr", "team_absent_days",
                "avg_team_working_hr",
                "team_actual_working_hr",
                "status",
                "absent_status"
            )

            

            total_absent_days = log.aggregate(total=Sum("team_absent_days"))
            response_dict["total_absent_days"] = total_absent_days.get("total") if total_absent_days else 0

            total_working_hr = log.aggregate(total=Sum("team_working_hr"))
            response_dict["total_working_hr"] = total_working_hr.get("total") if total_working_hr else 0

            total_actual_working_hr = log.aggregate(total=Sum("team_actual_working_hr"))
            response_dict["total_actual_working_hr"] = total_actual_working_hr.get("total") if total_actual_working_hr else 0

            total_employee = log.aggregate(total=Sum("employee_count"))
            response_dict["total_employee"] = total_employee.get("total") if total_employee else 0
            response_dict["working_hours_report"] = log.values("team", "status", "employee_count", "team_working_hr", "team_actual_working_hr")
            response_dict["absent_days_report"] = log.values("team","absent_status", "employee_count", "team_absent_days")

            if response_dict["total_working_hr"] > response_dict["total_actual_working_hr"] :
                response_dict["working_hr_status"] = "Overloaded"
            elif response_dict['total_working_hr'] < response_dict["total_actual_working_hr"]:
                response_dict["working_hr_status"] = "Underloaded"
            else:
                response_dict["working_hr_status"] = "Standard"


            if response_dict["total_absent_days"] >= 3:
                response_dict["absent_days_status"] = "Overloaded"
            elif response_dict["total_absent_days"] <= 1:
                response_dict["absent_days_status"] = "Standard"
            else:
                response_dict["absent_days_status"] = "Underloaded"
            


        elif csv_file.modules.module_identifier == 2:

            resource_status_list = [
                When(diff_res__lt=0, then=Value("Underloaded")),
                When(diff_res__gte=0.5, then=Value("Overloaded")),
                When(diff_res__gt=0, diff_res__lt=0.5, then=Value("Underloaded")),
                When(diff_res=0, then=Value("Standard")),
            ]

            standard_working_hour = csv_file.standard_working_hour
            if csv_file.working_type == "MONTH":
                standard_working_hour = standard_working_hour * 4
                
            tab = request.GET.get("tab", "Department")
            if tab == "Department":
                log  = CsvLogDetails.objects.filter(
                    uploaded_file__id=pk
                ).filter(
                    Q(uploaded_file__uploaded_by=request.user)|
                    Q(uploaded_file__uploaded_by__created_admin=request.user)
                ).values("department").annotate(
                    employee_count=Count("id"),
                    team_working_hr=Sum("working_hour"),
                    total_extra_hour=Sum("extra_hour"),
                    team_actual_working_hr=F("employee_count")*standard_working_hour
                ).annotate(
                    resource_required=F("team_working_hr")/standard_working_hour
                ).annotate(
                    diff_res=F("resource_required") - F("employee_count"),
                ).annotate(
                    resource_status=Case(
                        *resource_status_list, default=Value(""), output_field=CharField()
                    ),
                ).values(
                    "department", 
                    "employee_count",
                    "team_working_hr",
                    "total_extra_hour",
                    "team_actual_working_hr",
                    "resource_required",
                    "resource_status"
                )
                response_dict["working_hours_report"] = log.annotate(status=Case(
                        *status_list, default=Value(""), output_field=CharField()
                    )).values(
                    "department", "team_actual_working_hr",
                    "team_working_hr", "total_extra_hour",
                    "status"
                )
                res_report = tuple(log.annotate(status=F("resource_status")).values(
                    "department", "employee_count",
                    "resource_required",
                    "status"
                ))
                for i in res_report:
                    i["resource_required"] = round(i["resource_required"])
                response_dict["resource_status_report"] = res_report

                total_extra_hr = log.aggregate(total=Sum("total_extra_hour"))
                response_dict["total_extra_hr"] = total_extra_hr.get("total") if total_extra_hr else 0

                total_working_hr = log.aggregate(total=Sum("team_working_hr"))
                response_dict["total_working_hr"] = total_working_hr.get("total") if total_working_hr else 0

                total_actual_working_hr = log.aggregate(total=Sum("team_actual_working_hr"))
                response_dict["total_actual_working_hr"] = total_actual_working_hr.get("total") if total_actual_working_hr else 0
                
                total_employee = log.aggregate(total=Sum("employee_count"))
                total_resource = log.aggregate(total=Sum("resource_required"))
                response_dict["total_employee"] = total_employee.get("total") if total_employee else 0
                response_dict["total_resource"] = total_resource.get("total") if total_resource else 0


                if response_dict["total_working_hr"] > response_dict["total_actual_working_hr"] :
                    response_dict["working_hr_status"] = "Overloaded"
                elif response_dict['total_working_hr'] < response_dict["total_actual_working_hr"]:
                    response_dict["working_hr_status"] = "Underloaded"
                else:
                    response_dict["working_hr_status"] = "Standard"

                if response_dict["total_resource"] > response_dict["total_employee"] :
                    response_dict["resource_status"] = "Overloaded"
                elif response_dict['total_resource'] < response_dict["total_employee"]:
                    response_dict["resource_status"] = "Underloaded"
                else:
                    response_dict["resource_status"] = "Standard"
                
                if response_dict["total_extra_hr"] > 0 :
                    response_dict["extra_hr_status"] = "Overloaded"
                elif response_dict['total_extra_hr'] == 0:
                    response_dict["extra_hr_status"] = "Standard"
                else:
                    response_dict["extra_hr_status"] = "Underloaded"

            elif tab == "Team":
                select_department = request.GET.get("department")
                log  = CsvLogDetails.objects.filter(
                    uploaded_file__id=pk,
                    department=select_department
                ).filter(
                    Q(uploaded_file__uploaded_by=request.user)|
                    Q(uploaded_file__uploaded_by__created_admin=request.user)
                ).values("team").annotate(
                    employee_count=Count("id"),
                    team_working_hr=Sum("working_hour"),
                    total_extra_hour=Sum("extra_hour"),
                    team_actual_working_hr=F("employee_count")*standard_working_hour
                ).annotate(
                    resource_required=F("team_working_hr")/standard_working_hour
                ).annotate(
                    diff_res=F("resource_required") - F("employee_count"),
                ).annotate(
                    resource_status=Case(
                        *resource_status_list, default=Value(""), output_field=CharField()
                    ),
                ).values(
                    "team", 
                    "employee_count",
                    "team_working_hr",
                    "total_extra_hour",
                    "team_actual_working_hr",
                    "resource_required",
                    "resource_status"
                )
                response_dict["working_hours_report"] = log.annotate(status=Case(
                        *status_list, default=Value(""), output_field=CharField()
                    )).values(
                    "team", "team_actual_working_hr",
                    "team_working_hr", "total_extra_hour",
                    "status"
                )

                res_report = log.annotate(status=F("resource_status")).values(
                    "team", "employee_count",
                    "resource_required",
                    "status"
                )
                for i in res_report:
                    i["resource_required"] = round(i["resource_required"])

                response_dict["resource_status_report"] = res_report

                total_extra_hr = log.aggregate(total=Sum("total_extra_hour"))
                response_dict["total_extra_hr"] = total_extra_hr.get("total") if total_extra_hr else 0

                total_working_hr = log.aggregate(total=Sum("team_working_hr"))
                response_dict["total_working_hr"] = total_working_hr.get("total") if total_working_hr else 0

                total_actual_working_hr = log.aggregate(total=Sum("team_actual_working_hr"))
                response_dict["total_actual_working_hr"] = total_actual_working_hr.get("total") if total_actual_working_hr else 0
                
                total_employee = log.aggregate(total=Sum("employee_count"))
                total_resource = log.aggregate(total=Sum("resource_required"))
                response_dict["total_employee"] = total_employee.get("total") if total_employee else 0
                response_dict["total_resource"] = total_resource.get("total") if total_resource else 0


                if response_dict["total_working_hr"] > response_dict["total_actual_working_hr"] :
                    response_dict["working_hr_status"] = "Overloaded"
                elif response_dict['total_working_hr'] < response_dict["total_actual_working_hr"]:
                    response_dict["working_hr_status"] = "Underloaded"
                else:
                    response_dict["working_hr_status"] = "Standard"

                if response_dict["total_resource"] > response_dict["total_employee"] :
                    response_dict["resource_status"] = "Overloaded"
                elif response_dict['total_resource'] < response_dict["total_employee"]:
                    response_dict["resource_status"] = "Underloaded"
                else:
                    response_dict["resource_status"] = "Standard"
                
                if response_dict["total_extra_hr"] > 0 :
                    response_dict["extra_hr_status"] = "Overloaded"
                elif response_dict['total_extra_hr'] == 0:
                    response_dict["extra_hr_status"] = "Standard"
                else:
                    response_dict["extra_hr_status"] = "Underloaded"

            elif tab == "Designation":
                select_department = request.GET.get("department")
                select_team = request.GET.get("team")

                log  = CsvLogDetails.objects.filter(
                    uploaded_file__id=pk,
                    department=select_department,
                    team=select_team
                ).filter(
                    Q(uploaded_file__uploaded_by=request.user)|
                    Q(uploaded_file__uploaded_by__created_admin=request.user)
                ).values("designation").annotate(
                    employee_count=Count("id"),
                    team_working_hr=Sum("working_hour"),
                    total_extra_hour=Sum("extra_hour"),
                    team_actual_working_hr=F("employee_count")*standard_working_hour
                ).annotate(
                    resource_required=F("team_working_hr")/standard_working_hour
                ).annotate(
                    diff_res=F("resource_required") - F("employee_count"),
                ).annotate(
                    resource_status=Case(
                        *resource_status_list, default=Value(""), output_field=CharField()
                    ),
                ).values(
                    "designation", 
                    "employee_count",
                    "team_working_hr",
                    "total_extra_hour",
                    "team_actual_working_hr",
                    "resource_required"
                )

                response_dict["working_hours_report"] = log.annotate(status=Case(
                        *status_list, default=Value(""), output_field=CharField()
                    )).values(
                    "designation", "team_actual_working_hr",
                    "team_working_hr", "total_extra_hour",
                    "status"
                )

                res_report = log.annotate(status=F("resource_status")).values(
                    "designation", "employee_count",
                    "resource_required",
                    "status"
                )
                for i in res_report:
                    i["resource_required"] = round(i["resource_required"])

                response_dict["resource_status_report"] = res_report

                total_extra_hr = log.aggregate(total=Sum("total_extra_hour"))
                response_dict["total_extra_hr"] = total_extra_hr.get("total") if total_extra_hr else 0

                total_working_hr = log.aggregate(total=Sum("team_working_hr"))
                response_dict["total_working_hr"] = total_working_hr.get("total") if total_working_hr else 0

                total_actual_working_hr = log.aggregate(total=Sum("team_actual_working_hr"))
                response_dict["total_actual_working_hr"] = total_actual_working_hr.get("total") if total_actual_working_hr else 0
                
                total_employee = log.aggregate(total=Sum("employee_count"))
                total_resource = log.aggregate(total=Sum("resource_required"))
                response_dict["total_employee"] = total_employee.get("total") if total_employee else 0
                response_dict["total_resource"] = total_resource.get("total") if total_resource else 0


                if response_dict["total_working_hr"] > response_dict["total_actual_working_hr"] :
                    response_dict["working_hr_status"] = "Overloaded"
                elif response_dict['total_working_hr'] < response_dict["total_actual_working_hr"]:
                    response_dict["working_hr_status"] = "Underloaded"
                else:
                    response_dict["working_hr_status"] = "Standard"

                if response_dict["total_resource"] > response_dict["total_employee"] :
                    response_dict["resource_status"] = "Overloaded"
                elif response_dict['total_resource'] < response_dict["total_employee"]:
                    response_dict["resource_status"] = "Underloaded"
                else:
                    response_dict["resource_status"] = "Standard"
                
                if response_dict["total_extra_hr"] > 0 :
                    response_dict["extra_hr_status"] = "Overloaded"
                elif response_dict['total_extra_hr'] == 0:
                    response_dict["extra_hr_status"] = "Standard"
                else:
                    response_dict["extra_hr_status"] = "Underloaded"

        elif csv_file.modules.module_identifier == 3:
            monthly_revenue = csv_file.monthly_revenue
            monthly_revenue_cal = monthly_revenue/100
            weightage_data = DepartmentWeightage.objects.filter(
                uploaded_file=csv_file,
                department=OuterRef("department")
            ).values("percentage")
            my_log_cost  = CsvLogDetails.objects.filter(
                uploaded_file__id=pk
            ).filter(
                Q(uploaded_file__uploaded_by=request.user)|
                Q(uploaded_file__uploaded_by__created_admin=request.user)
            ).aggregate(total_cost=Sum("total_pay"))
            total_my_cost = 0
            if my_log_cost:
                total_my_cost = my_log_cost.get("total_cost")

            status_list = [
                When(rc_coe__gte=0, rc_coe__lte=3, then=Value("Low")),
                When(rc_coe__gt=3, rc_coe__lte=4, then=Value("Medium")),
                When(rc_coe__gt=5,then=Value("High")),
            ]

            log  = CsvLogDetails.objects.filter(
                uploaded_file__id=pk
            ).filter(
                Q(uploaded_file__uploaded_by=request.user)|
                Q(uploaded_file__uploaded_by__created_admin=request.user)
            ).values("department").annotate(
                employee_count=Count("id"),
                v_chain=Value("A"),
                cost_of_employee=Sum("total_pay"),
                weightage=Subquery(weightage_data),
                status=Value("Overloaded")
            ).annotate(
                revenue_contribution=monthly_revenue_cal*F("weightage"),
                cost_contribution=(F("cost_of_employee")/total_my_cost)*100
            ).annotate(
                rc_coe=F("revenue_contribution")/F("cost_of_employee")
            ).annotate(
                score=Case(
                    *status_list, default=Value(""), output_field=CharField()
                ),
            ).values(
                "department", 
                "employee_count",
                "v_chain",
                "cost_of_employee",
                "weightage",
                "revenue_contribution",
                "cost_contribution",
                "rc_coe",
                "score",
                "status"
            )
            response_dict["report"] = log.values("department", "status", "score", "rc_coe","cost_contribution", "revenue_contribution", "employee_count", "v_chain", "cost_of_employee", "weightage")

        elif csv_file.modules.module_identifier == 4:
            log  = CsvLogDetails.objects.filter(
                uploaded_file__id=pk
            ).filter(
                Q(uploaded_file__uploaded_by=request.user)|
                Q(uploaded_file__uploaded_by__created_admin=request.user)
            ).values("department").annotate(
                employee_count=Count("id"),
                total_gross_pay=Sum("gross_pay"),
                total_fixed_pay=Sum("fixed_pay"),
                total_varriable_pay=Sum("varriable_pay"),
                total_overtime_pay=Sum("overtime_pay"),
                total_varriable=Sum("varriable_pay"),
                total_holidays=Sum("no_of_holiday"),
                avg_rate=Avg("hourly_rate")
            ).annotate(
                additional_cost=(F("total_varriable")/F("total_fixed_pay"))*100,
                total_holiday_pay=F("total_holidays")*F("avg_rate")
            ).values(
                "department", 
                "employee_count",
                "total_gross_pay",
                "total_fixed_pay",
                "total_varriable_pay",
                "total_overtime_pay",
                "total_holiday_pay",
                "additional_cost"
            )
            response_dict["report"] = tuple(log)

        elif csv_file.modules.module_identifier == 5:
            select_country = request.GET.get("select_country")
            select_department = request.GET.get("select_department")
            select_designation = request.GET.get("select_designation")
            select_experience = request.GET.get("select_experience")

            log  = CsvLogDetails.objects.filter(
                uploaded_file__id=pk
            ).filter(
                Q(uploaded_file__uploaded_by=request.user)|
                Q(uploaded_file__uploaded_by__created_admin=request.user)
            ).values("region").annotate(
                male_count=Count(Case(When(
                    gender__in=["MALE", "Male", "male"],then=F("sl_no")
                ))),
                female_count=Count(Case(When(
                    gender__in=["FEMALE", "Female", "female"], then=F("sl_no")
                ))),
                total_count=Count("sl_no")
            ).annotate(
                male=ExpressionWrapper(F("male_count")*100.0/F("total_count")*1.0, output_field=FloatField()),
                female=ExpressionWrapper(F("female_count")*100/F("total_count")*1.0, output_field=FloatField())
            ).values(
                "region", 
                "male",
                "female",
            )

            individual_report = CsvLogDetails.objects.filter(
                uploaded_file__id=pk
            ).filter(
                Q(uploaded_file__uploaded_by=request.user)|
                Q(uploaded_file__uploaded_by__created_admin=request.user)
            )
            if select_country:
                individual_report = individual_report.filter(region=select_country)
            if select_department:
                individual_report = individual_report.filter(department=select_department)
            if select_designation:
                individual_report = individual_report.filter(designation=select_designation)
            if select_experience:
                individual_report = individual_report.filter(experience=select_experience)

            if select_country:
                male_count = 0
                female_count= 0
                male_pay= 0
                female_pay = 0
                total_gap = 0
                individual_report = individual_report.aggregate(
                    male_count=Count(Case(When(gender__in=["MALE", "Male", "male"],then=F("sl_no")))),
                    female_count=Count(Case(When(gender__in=["FEMALE", "Female", "female"],then=F("sl_no")))),
                    male_pay=Avg(Case(When(gender__in=["MALE", "Male", "male"],then=F("fixed_pay")))),
                    female_pay=Avg(Case(When(gender__in=["FEMALE", "Female", "female"],then=F("fixed_pay")))),
                    total=Count("sl_no")
                )
                if individual_report:
               
                    male_count = individual_report["male_count"] or 0
                    male_count = round(male_count*100/individual_report["total"], 1) if individual_report["total"] !=0 else 0

                    female_count = individual_report["female_count"] or 0
                    female_count = round(female_count*100/individual_report["total"], 1) if individual_report["total"] !=0 else 0

                    female_pay = round(individual_report["female_pay"] or 0,1)
                    male_pay = round(individual_report["male_pay"] or 0,1)

                    total_gap = female_pay - male_pay
                    if total_gap <0 :
                        total_gap = total_gap * -1

                individual_report_date = {
                    "male":male_count,
                    "female":female_count,
                    "male_pay":male_pay,
                    "female_pay":female_pay,
                    "pay_gap":total_gap
                }
                response_dict["individual_report"] = individual_report_date

            response_dict["region_report"] = tuple(log)

        elif csv_file.modules.module_identifier == 6:
            select_department = request.GET.get("select_department")
            select_tab = request.GET.get("select_tab", "downtime_overview")

            if select_tab == "downtime_overview":
                if not select_department:
                    response_dict["error"] = "Please select department"
                    return Response(response_dict, status=status.HTTP_200_OK)

                log  = CsvLogDetails.objects.filter(
                    uploaded_file__id=pk,
                    department=select_department
                ).filter(
                    Q(uploaded_file__uploaded_by=request.user)|
                    Q(uploaded_file__uploaded_by__created_admin=request.user)
                ).values("factors_effected").annotate(
                    numbers=Sum("downtime_week"),
                ).values(
                    "factors_effected", 
                    "numbers",
                )

                
                total_order_loss_per_week = []
                peak_sale = CsvLogDetails.objects.filter(
                    uploaded_file__id=pk,
                    department=select_department,
                    factors_effected__in=["Sales impact downtime ", "Sales impact downtime"],
                    impact_hour__in=["peak", "peak "]
                ).aggregate(tot=Sum("downtime_week"))
                non_peak_sale = CsvLogDetails.objects.filter(
                    uploaded_file__id=pk,
                    department=select_department,
                    factors_effected__in=["Sales impact downtime ", "Sales impact downtime"],
                    impact_hour__in=["No -peak ", "No -peak", "No-peak"]
                ).aggregate(tot=Sum("downtime_week"))

                total_cost_impact = CsvLogDetails.objects.filter(
                    uploaded_file__id=pk,
                    department=select_department,
                    factors_effected__in=["cost impact downtime ", "cost impact downtime"],
                ).aggregate(tot=Sum("downtime_week"))

                sales_impact_down = CsvLogDetails.objects.filter(
                    uploaded_file__id=pk,
                    department=select_department,
                    factors_effected__in=["Sales impact downtime ", "Sales impact downtime"],
                ).aggregate(tot=Sum("downtime_week"))

                peak_sale_val = peak_sale.get("tot") if peak_sale and peak_sale.get("tot") else 0
                non_peak_sale_val = non_peak_sale.get("tot") if non_peak_sale and non_peak_sale.get("tot") else 0

                sales_impact_down = sales_impact_down.get("tot") if sales_impact_down.get("tot") else 0
                try:
                    peak_sale_val = float(sales_impact_down)/(float(csv_file.peak_hour_sale_value)*7)
                except:
                    peak_sale_val = 0
                peak_sale_val = peak_sale_val * float(csv_file.peak_hour_sale_hr)

        
                try:
                    non_peak_sale_val = float(sales_impact_down)/(float(csv_file.non_peak_hour_sale_value)*7)
                except:
                    non_peak_sale_val = 0
                non_peak_sale_val = non_peak_sale_val * float(csv_file.non_peak_hour_sale_hr)


                total_target = csv_file.non_peak_hour_sale_value + csv_file.peak_hour_sale_value
                total_cost_impact_val = total_cost_impact.get("tot") if total_cost_impact.get("tot") else 0
                try:
                    total_cost_impact_val = float(total_cost_impact_val)/(float(total_target)*7)
                except:
                    total_cost_impact_val = 0

              
                total_cost_impact_val = total_cost_impact_val * float(csv_file.employee_cost_target)

                res_cal = total_cost_impact.get("tot") if total_cost_impact.get("tot") else 0 
                res_total = total_target * 7
          
                resource_utilisation = res_cal/ res_total if res_total != 0 else 0
                resource_utilisation = resource_utilisation *100
                peak_sale_val = peak_sale_val * -1
                non_peak_sale_val = non_peak_sale_val * -1
                total_cost_impact_val = total_cost_impact_val * -1
                resource_utilisation = resource_utilisation *-1

                availability  = tuple(CsvLogDetails.objects.filter(
                    uploaded_file__id=pk,
                    department=select_department
                ).filter(
                    Q(uploaded_file__uploaded_by=request.user)|
                    Q(uploaded_file__uploaded_by__created_admin=request.user)
                ).values("system_name").annotate(
                    numbers=Sum("downtime_week"),
                ).values(
                    "system_name", 
                    "numbers",
                ))
                availability_dict = []
                total_target = total_target * 7
                for i in availability:
                    if total_target != 0:
                        cal = i.get("numbers")*100/total_target
                    else:
                        cal = 0
                    percentage = 100 - cal
                    res_status = "Standard"
                    if percentage > 90:
                        res_status = "Standard"
                    elif percentage > 50:
                        res_status = "Overloaded"
                    elif percentage < 50:
                        res_status = "Underloaded"
                    availability_dict.append(
                        {
                            "system_name":i.get("system_name"),
                            "percentage":percentage,
                            "status":res_status
                        }
                    )


                total_order_loss_per_week.append(
                    {
                        "parameter": "Total order loss for the week",
                        "number":round(non_peak_sale_val,1) + round(peak_sale_val,1)
                    }
                )
                total_order_loss_per_week.append(
                    {
                        "parameter": "Peak Hour Sale Loss",
                        "number":round(peak_sale_val,1)
                    }
                )
                total_order_loss_per_week.append(
                    {
                        "parameter": "Non-Peak Hour Sale Loss",
                        "number":round(non_peak_sale_val,1)
                    }
                )
                total_order_loss_per_week.append(
                    {
                        "parameter": "Total cost impact of resource",
                        "number":round(total_cost_impact_val,1)
                    }
                )
                total_order_loss_per_week.append(
                    {
                        "parameter": "Resource utilisation impact",
                        "number":round(resource_utilisation, 2)
                    }
                )
                

                total_downtime_per_week = []
                total_down = 0
                for i in log:
                    if i.get("numbers"):
                        total_down = total_down + int(i.get("numbers"))
                    total_downtime_per_week.append(
                        {
                           "factors_effected":i.get("factors_effected"),
                           "numbers":i.get("numbers")
                        }
                    )

                total_downtime_per_week.append(
                    {
                        "factors_effected":"Total Down-Time Per Week",
                        "numbers":total_down,
                    }
                )
                response_dict["total_downtime_per_week"] = total_downtime_per_week
                response_dict["total_order_loss_per_week"] = total_order_loss_per_week
                response_dict["software_availability"]    = availability_dict
            elif select_tab == "total_downtime":
                status_list = [
                    When(numbers__gt=10, then=Value("Overloaded")),
                    When(numbers__lt=10,numbers__gte=5, then=Value("Underloaded")),
                    When(numbers__lt=5, then=Value("Standard")),
                ]
                log  = CsvLogDetails.objects.filter(
                    uploaded_file__id=pk,
                ).filter(
                    Q(uploaded_file__uploaded_by=request.user)|
                    Q(uploaded_file__uploaded_by__created_admin=request.user)
                ).values("department").annotate(
                    numbers=Sum("downtime_week", default=0),
                ).annotate(
                    status=Case(
                        *status_list, default=Value("Standard"), output_field=CharField()
                    ),
                ).values(
                    "department", 
                    "numbers",
                    "status"
                )

                sales_log  = CsvLogDetails.objects.filter(
                    uploaded_file__id=pk,
                    factors_effected__in=["Sales impact downtime ", "Sales impact downtime"],
                ).filter(
                    Q(uploaded_file__uploaded_by=request.user)|
                    Q(uploaded_file__uploaded_by__created_admin=request.user)
                ).values("department").annotate(
                    numbers=Sum("downtime_week", default=0),
                ).annotate(
                    status=Case(
                        *status_list, default=Value("Standard"), output_field=CharField()
                    ),
                ).values(
                    "department", 
                    "numbers",
                    "status"
                )
                cost_log  = CsvLogDetails.objects.filter(
                    uploaded_file__id=pk,
                    factors_effected__in=["cost impact downtime ", "cost impact downtime"],
                ).filter(
                    Q(uploaded_file__uploaded_by=request.user)|
                    Q(uploaded_file__uploaded_by__created_admin=request.user)
                ).values("department").annotate(
                    numbers=Sum("downtime_week", default=0),
                ).annotate(
                    status=Case(
                        *status_list, default=Value("Standard"), output_field=CharField()
                    ),
                ).values(
                    "department", 
                    "numbers",
                    "status"
                )
                other_log  = CsvLogDetails.objects.filter(
                    uploaded_file__id=pk,
                    factors_effected__in=["other impact downtime ", "other impact downtime"],
                ).filter(
                    Q(uploaded_file__uploaded_by=request.user)|
                    Q(uploaded_file__uploaded_by__created_admin=request.user)
                ).values("department").annotate(
                    numbers=Sum("downtime_week", default=0),
                ).annotate(
                    status=Case(
                        *status_list, default=Value("Standard"), output_field=CharField()
                    ),
                ).values(
                    "department", 
                    "numbers",
                    "status"
                )

                response_dict["total_downtime_per_week"] = tuple(log)
                response_dict["sales_impact_downtime"] = tuple(sales_log)
                response_dict["cost_impact_downtime"] = tuple(cost_log)
                response_dict["other_impact_downtime"] = tuple(other_log)
        
        
        elif csv_file.modules.module_identifier == 10:

            trucks_required_dict = []
            trucks_required  = tuple(CsvLogDetails.objects.filter(
                uploaded_file__id=pk,
            ).filter(
                Q(uploaded_file__uploaded_by=request.user)|
                Q(uploaded_file__uploaded_by__created_admin=request.user)
            ).values("location").annotate(
                total_actual=Sum("actual"),
                total_truck=Sum("no_of_truck_required"),
                total_capacity=Sum("total_required_capacity"),
                total_actual_cal=Sum("actual_calculated"),
                total_revenue=Sum("per_ton_revenue_loss"),
                total_vehicle=Sum("vehicle_utilisation"),

            ).values(
                "total_actual", 
                "total_truck",
                "location",
                "total_actual_cal",
                "total_capacity",
                "total_revenue",
                "total_vehicle"
            ))
            payload_drop_dict = []
            revenue_drop_dict = []
            vehicle_dict = []
            monthly_vehicle_report = []

            total_actual = 0
            total_truck = 0
            total_capa = 0
            total_actual_cal = 0
            total_revenue = 0
            total_vehicle = 0

            for i in trucks_required:
                truck_required = 0
                if i.get("total_truck",0) != 0:
                    truck_required = round(float(i.get("total_actual",0))*100/float(i.get("total_truck",0)), 2)
                total_actual = total_actual + i.get("total_actual", 0)
                total_truck = total_truck + i.get("total_truck", 0)

                if truck_required < 60:
                    status_tr = "Overloaded"
                elif truck_required < 90:
                    status_tr = "Underloaded"
                else:
                    status_tr = "Standard"

                trucks_required_dict.append(
                    {
                        "no_of_truck_required":truck_required,
                        "location":i.get("location"),
                        "status":status_tr
                    }
                )

                pay = i.get("total_capacity", 0)- i.get("total_actual_cal", 0)
                pay_cal = pay/i.get("total_capacity", 0) if i.get("total_capacity", 0) != 0 else 0
                
                total_capa = total_capa + i.get("total_capacity", 0)
                total_actual_cal = total_actual_cal + i.get("total_actual_cal", 0)

                if round(pay_cal *100, 2) < 60:
                    status_p = "Overloaded"
                elif round(pay_cal *100, 2) < 90:
                    status_p = "Underloaded"
                else:
                    status_p = "Standard"

                payload_drop_dict.append(
                    {
                        "payload_drop":round(pay_cal *100, 2),
                        "location":i.get("location"),
                        "status":status_p
                    }
                )

                total_revenue = total_revenue + i.get("total_revenue", 0)
                revenue_cal = (i.get("total_capacity", 0) * 1000)*2
                revenue_cal = i.get("total_revenue", 0) / revenue_cal if revenue_cal != 0  else 0
                
                if round(revenue_cal *100, 2) < 60:
                    status_r = "Overloaded"
                elif round(revenue_cal *100, 2) < 90:
                    status_r = "Underloaded"
                else:
                    status_r = "Standard"
                revenue_drop_dict.append(
                    {
                        "revenue_drop":round(revenue_cal *100, 2),
                        "location":i.get("location"),
                        "status":status_r
                    }
                )

                total_vehicle = total_vehicle + i.get("total_vehicle", 0)
                veh_cal = i.get("total_vehicle", 0) / float(csv_file.no_of_days)

                if round(veh_cal *100, 2) < 60:
                    status_v = "Overloaded"
                elif round(veh_cal *100, 2) < 90:
                    status_v = "Underloaded"
                else:
                    status_v = "Standard"

                vehicle_dict.append(
                    {
                        "vehicle_utilisation":round(veh_cal *100, 2),
                        "location":i.get("location"),
                        "status":status_v
                    }
                )


                monthly_vehicle_report.append(
                    {
                        "no_of_truck_required":truck_required,
                        "payload_drop":round(pay_cal *100, 2),
                        "revenue_drop":round(revenue_cal *100, 2),
                        "vehicle_utilisation":round(veh_cal *100, 2),
                        "location":i.get("location"),
                        "status":status_v
                    }
                )


            tr_total = total_actual*100/total_truck if total_truck != 0 else 0
            if round(tr_total, 2) < 60:
                status_v = "Overloaded"
            elif round(tr_total, 2) < 90:
                status_v = "Underloaded"
            else:
                status_v = "Standard"
            trucks_required_dict.append(
                {
                    "no_of_truck_required":round(tr_total, 2),
                    "location":"Total",
                    "status":status_v
                }
            )

            p_total = (total_capa - total_actual_cal)/total_capa if total_capa != 0 else 0
            if round(p_total *100, 2) < 60:
                status_v = "Overloaded"
            elif round(p_total *100, 2) < 90:
                status_v = "Underloaded"
            else:
                status_v = "Standard"
            payload_drop_dict.append(
                {
                    "payload_drop":round(p_total *100, 2),
                    "location":"Total",
                    "status":status_v
                }
            )

            t_total = (total_capa * 1000)*2
            total = total_revenue/t_total if t_total !=0 else 0
            if round(total *100, 2) < 60:
                status_v = "Overloaded"
            elif round(total *100, 2) < 90:
                status_v = "Underloaded"
            else:
                status_v = "Standard"
            revenue_drop_dict.append(
                {
                    "revenue_drop":round(total *100, 2),
                    "location":"Total",
                    "status":status_v
                }
            )

            total_vehicle = total_vehicle / len(trucks_required)
            v_total = total_vehicle/float(csv_file.no_of_days) if float(csv_file.no_of_days) !=0 else 0
            if round(v_total *100, 2) < 60:
                status_v = "Overloaded"
            elif round(v_total *100, 2) < 90:
                status_v = "Underloaded"
            else:
                status_v = "Standard"
            vehicle_dict.append(
                {
                    "vehicle_utilisation":round(v_total *100, 2),
                    "location":"Total",
                    "status":status_v
                }
            )
            monthly_vehicle_report.append(
                {
                    "no_of_truck_required":round(tr_total, 2),
                    "payload_drop":round(p_total *100, 2),
                    "revenue_drop":round(total *100, 2),
                    "vehicle_utilisation":round(v_total *100, 2),
                    "location":"Total",
                    "status":status_v
                }
            )
            response_dict["trucks_required"]    = trucks_required_dict
            response_dict["payload_drop"]    = payload_drop_dict
            response_dict["revenue_drop"]    = revenue_drop_dict
            response_dict["vehicle_utilisation"]    = vehicle_dict
            response_dict["monthly_vehicle_report"]    = monthly_vehicle_report

        
        elif csv_file.modules.module_identifier == 8:
            select_department = request.GET.get("select_department")
            select_level = request.GET.get("select_level", 100)
            
            perc = 1
            if select_level == 100 or select_level == "100":
                perc = csv_file.automation_100/100
            if select_level == 75 or select_level == "75":
                perc = csv_file.automation_75/100
            if select_level == 50 or select_level == "50":
                perc = csv_file.automation_50/100
            if select_level == 30 or select_level == "30":
                perc = csv_file.automation_30/100


            log  = CsvLogDetails.objects.filter(
                uploaded_file__id=pk
            )
            if select_department:
                log = log.filter(department=select_department)

            status_list = [
                When(payback_period__lt=3, then=Value("Green functional area budget")),
                When(payback_period__gte=3, payback_period__lte=5, then=Value("Green Department Budget")),
                When(payback_period__gt=5 ,then=Value("Green Operational Budget")),
            ]

            log  = log.filter(
                uploaded_file__id=pk
            ).values("department").annotate(
                total_employees=Sum("no_of_resource_required"),
                average_pay=Value(csv_file.average_pay_per_employee),
                total_software_cost=Sum("software_cost"),
            ).annotate(
                total_manpower=F("total_employees") * 160 * 12,
                total_cost_employee=F("total_employees")*F("average_pay")
            ).annotate(
                resource_savings=F("total_cost_employee")*perc
            ).annotate(
                employee_saved=F("resource_savings")/F("average_pay"),
                payback_period=F("total_software_cost")/F("resource_savings"),
            ).annotate(
                status=Case(
                    *status_list, default=Value(""), output_field=CharField()
                ),
            ).values(
                "department", 
                "total_employees",
                "total_manpower",
                "average_pay",
                "total_software_cost",
                "resource_savings",
                "total_cost_employee",
                "employee_saved",
                "payback_period",
                "status"
            )
            if not log:
                log = {
                    "department":select_department,
                    "total_employees":0,
                    "total_manpower":0,
                    "average_pay":0,
                    "total_software_cost":0,
                    "resource_savings":0,
                    "total_cost_employee":0,
                    "employee_saved":0,
                    "payback_period":0,
                    "status":""
                }
            else:
                log = log[0]
            
            
            response_dict["report"] = log
        elif csv_file.modules.module_identifier == 9:
            report = []

    
            avg_order_per_hour = float(csv_file.total_orders_pay_day)/float(csv_file.operating_hours_day) if csv_file.operating_hours_day != 0 else 0
            no_of_res = avg_order_per_hour/12
            productivity_varriation_cal = float(csv_file.actual_resource_per_hour)/no_of_res if no_of_res !=0  else 0
            productivity_varriation_cal2 = float(csv_file.total_orders_pay_day)/float(csv_file.productivity_varriation) if csv_file.productivity_varriation !=0  else 0
            productivity_varriation = productivity_varriation_cal * productivity_varriation_cal2
            report.append(
                {
                    "per_day_value":"PRODUCTIVITY VARIATION (WAREHOUSE)",
                    "target":csv_file.productivity_varriation,
                    "actual":round(productivity_varriation*100, 3)
                }
            )

            lead_time = csv_file.lead_time
            if no_of_res > csv_file.actual_resource_per_hour:
                lead_time_v1 = no_of_res - csv_file.actual_resource_per_hour
                lead_time_v2 = lead_time_v1 * 60
                lead_time_v3 = lead_time_v2/lead_time if lead_time != 0  else 0

                lead_time_v4 = lead_time/csv_file.actual_resource_per_hour if csv_file.actual_resource_per_hour != 0 else 0
                lead_time_v5 = lead_time_v3 * lead_time_v4
            report.append(
                {
                    "per_day_value":"LEAD TIME (AT WAREHOUSE)",
                    "target":csv_file.lead_time,
                    "actual":lead_time_v5
                }
            )
            resource_additional_cost_cal = (csv_file.temporary_man_cost - csv_file.cost_per_man)*csv_file.temporary_man_arranged
            report.append(
                {
                    "per_day_value":"RESOURCES ADDITIONAL COST",
                    "target":csv_file.resource_additional_cost,
                    "actual":round(resource_additional_cost_cal)
                }
            )
            shortage_of_manpower_cal = float(csv_file.total_orders_pay_day)*1.1/12
            tot_res = float(csv_file.actual_resource_per_day)+float(csv_file.temporary_man_arranged)
            shortage_of_manpower = shortage_of_manpower_cal - tot_res
            report.append(
                {
                    "per_day_value":"SHORTAGE OF MANPOWER",
                    "target":csv_file.shortage_of_manpower,
                    "actual":round(shortage_of_manpower)
                }
            )

            sqft_allocation = csv_file.workhouse_space/tot_res if tot_res != 0 else 0
            report.append(
                {
                    "per_day_value":"SQUARE FEET ALLOCATION PER RESOURCE",
                    "target":csv_file.sqft_allocation,
                    "actual":round(sqft_allocation)
                }
            )

            order_loss_cal = csv_file.productivity_varriation * (productivity_varriation*100)
            order_loss_cal = order_loss_cal/100
            order_loss = order_loss_cal - csv_file.productivity_varriation
            report.append(
                {
                    "per_day_value":"ORDER LOSS",
                    "target":csv_file.order_loss,
                    "actual":round(order_loss)
                }
            )
            cost_per_shipment_v1 = csv_file.actual_resource_per_day - csv_file.temporary_man_arranged
            cost_per_shipment_v2 = cost_per_shipment_v1 * csv_file.cost_per_man
            cost_per_shipment_v3 = csv_file.temporary_man_arranged * csv_file.temporary_man_cost
            cost_per_shipment_v4 = cost_per_shipment_v2 + cost_per_shipment_v3
            cost_per_shipment_v5 = order_loss_cal
            cost_per_shipment_v6 = cost_per_shipment_v4 / cost_per_shipment_v5 if cost_per_shipment_v5 != 0 else 0
            report.append(
                {
                    "per_day_value":"COST PER SHIPMENT PROCESSING",
                    "target":csv_file.cost_per_shipment,
                    "actual":round(cost_per_shipment_v6, 4)
                }
            )
            report.append(
                {
                    "per_day_value":"DELAY DURATION",
                    "target":csv_file.delay_duration,
                    "actual":lead_time_v5 - csv_file.lead_time
                }
            )

            
            response_dict["report"]    = report

        elif csv_file.modules.module_identifier == 7:
            report1 = {}
            report2 = {}
            report3 = {}

            total_no_of_working_days = csv_file.total_working_days
            number_of_employees = log  = CsvLogDetails.objects.filter(
                uploaded_file__id=pk,
            ).count()
            avg_availability = CsvLogDetails.objects.filter(
                uploaded_file__id=pk,
            ).aggregate(avg=Avg("employee_availability"))
            avg_conversion = CsvLogDetails.objects.filter(
                uploaded_file__id=pk,
            ).aggregate(avg=Avg("conversion_rate"))
            total_call_per_day = CsvLogDetails.objects.filter(
                uploaded_file__id=pk,
            ).aggregate(tot=Sum("calls_per_hour"))

            total_call_per_day = total_call_per_day.get("tot") if total_call_per_day else 0
            employee_availability = avg_availability.get("avg") if avg_availability else 0
            avg_conversion =  avg_conversion.get("avg") if avg_conversion else 0

            working_hours_aligned_with_required_availability = number_of_employees * csv_file.working_hour_per_day * total_no_of_working_days
            avg_call_per_month = csv_file.average_call_per_day * csv_file.working_days
            actual_resource_working_hour = number_of_employees * csv_file.working_hour_per_day * total_no_of_working_days
            actual_resource_working_hour = (actual_resource_working_hour * employee_availability)/100
            overtime_hours_required = working_hours_aligned_with_required_availability - actual_resource_working_hour
            no_of_resource_required = overtime_hours_required/48

        
            avg_sale_order_per_day_based_on_availability = total_call_per_day * csv_file.working_hour_per_day
            avg_sale_order_per_day_based_on_availability = (avg_sale_order_per_day_based_on_availability * employee_availability)/100
            avg_conversion = (avg_sale_order_per_day_based_on_availability * avg_conversion )/100
            avg_sale_order_per_day_based_on_availability = avg_conversion/ csv_file.completed_days if csv_file.completed_days != 0 else 0
 
            actual_daily_call_avg = (csv_file.average_call_per_day * employee_availability)/100
            actual_daily_call_avg = (actual_daily_call_avg * csv_file.process)/100
            actual_daily_call_avg = (actual_daily_call_avg * csv_file.technology)/100 
            order_achieved_till = csv_file.completed_days * avg_sale_order_per_day_based_on_availability
    
            outstanding_order_count = csv_file.sales_target_in_terms - order_achieved_till
            avg_daily_order_for_target_achievement = outstanding_order_count / csv_file.no_of_days_left if csv_file.no_of_days_left != 0 else 0
            sale_estimate = avg_sale_order_per_day_based_on_availability * csv_file.working_days
            revenue = sale_estimate / csv_file.sales_target_in_terms if csv_file.sales_target_in_terms != 0 else 0
            revenue = revenue * 100

            revenue_till_date = csv_file.average_rate_per_sale * avg_sale_order_per_day_based_on_availability * csv_file.completed_days
            revenue_estimate = csv_file.average_rate_per_sale * sale_estimate
            log = CsvLogDetails.objects.filter(
                uploaded_file__id=pk,
            ).values("center_name").annotate(
                total_conversion_rate=Avg("conversion_rate"),
                total_call_drop_rate=Avg("call_drop_rate"),
                total_transaction_rate=Avg("transaction_rate"),
                varriation_in_call_drop_rate=Max("call_drop_rate") - Min("call_drop_rate"),
                variation_in_transaction_drop_rate=Max("transaction_rate") - Min("transaction_rate")
            ).values("center_name", "total_conversion_rate", "total_call_drop_rate", "total_transaction_rate", "varriation_in_call_drop_rate", "variation_in_transaction_drop_rate")
            
            variation_in_call_drop_rate = 7
            variation_in_transaction_drop_rate = 7

            report1["avg_call_per_day"] = csv_file.average_call_per_day
            report1["process"] = csv_file.process
            report1["technology"] = csv_file.technology
            report1["avg_daily_order_for_target_achievement"] = avg_daily_order_for_target_achievement
            report1["actual_daily_call_avg"] = actual_daily_call_avg
            report1["outstanding_order_count"] = outstanding_order_count
            report1["no_of_resource_required"] = no_of_resource_required
            report1["overtime_hours_required"] = overtime_hours_required
            report1["actual_resource_working_hour"] = actual_resource_working_hour
            report1["avg_call_per_month"] = avg_call_per_month
            report1["total_no_of_working_days"] = total_no_of_working_days
            report1["working_hours_aligned_with_required_availability"] = working_hours_aligned_with_required_availability
            

            report2["working_days"] = csv_file.working_days
            report2["no_of_days_left"] = csv_file.no_of_days_left
            report2["working_hour_per_day"] = csv_file.working_hour_per_day
            report2["sales_target_in_terms"] = csv_file.sales_target_in_terms
            report2["average_rate_per_sale"] = csv_file.average_rate_per_sale
            report2["number_of_employee"] = number_of_employees
            report2["required_availability"] = csv_file.required_availability
            report2["avg_sale_order_per_day_based_on_availability"] = avg_sale_order_per_day_based_on_availability
            report2["employee_availability"] = employee_availability
            report2["completed_days"] = csv_file.completed_days
            report2["order_achieved_till_date"] = order_achieved_till
            report2["sale_estimate"] = sale_estimate
            report2["target_achieve"] = revenue
            report2["revenue_till_date"] = revenue_till_date
            report2["revenue_estimate"] = revenue_estimate

            response_dict["report1"]    = report1
            response_dict["report2"]    = report2
            response_dict["report3"]    = log

            response_dict["variation_in_call_drop_rate"] = 0
            response_dict["variation_in_transaction_drop_rate"] = 0

        elif csv_file.modules.module_identifier == 11:
            report1 = {}
            report2 = {}
            report3 = {}
            number_of_employees = CsvLogDetails.objects.filter(
                uploaded_file__id=pk,
            ).count()
            avg_availability = CsvLogDetails.objects.filter(
                uploaded_file__id=pk,
            ).aggregate(avg=Avg("employee_availability"))
            avg_cx = CsvLogDetails.objects.filter(
                uploaded_file__id=pk,
            ).aggregate(avg=Avg("cx_call_no_response"))
            avg_non = CsvLogDetails.objects.filter(
                uploaded_file__id=pk,
            ).aggregate(avg=Avg("non_resloution"))
            total_call_per_day = CsvLogDetails.objects.filter(
                uploaded_file__id=pk,
            ).aggregate(tot=Sum("calls_per_hour"))
            total_call_per_day = total_call_per_day.get("tot") if total_call_per_day else 0
            working_hours_aligned_with_required_availability = number_of_employees * csv_file.working_hour_per_day * 6
            avg_cx = avg_cx.get("avg") if avg_cx else 0
            avg_non = avg_non.get("avg") if avg_non else 0

            employee_availability = avg_availability.get("avg") if avg_availability else 0
            actual_resource_working_hour = number_of_employees * csv_file.working_hour_per_day * csv_file.working_days_per_week
            actual_resource_working_hour = (actual_resource_working_hour * employee_availability)/100
            overtime_hours_required = working_hours_aligned_with_required_availability - actual_resource_working_hour
            no_of_resource_required = overtime_hours_required/48
            

            perc = employee_availability/100
            call_hanlde = csv_file.call_handle_process / 100
            technology = csv_file.technology / 100

            daily_call_average = total_call_per_day * perc * csv_file.working_hour_per_day
            process_and_technology_driven = daily_call_average * call_hanlde * technology * perc
            total_estimated_call = csv_file.average_call_per_day * csv_file.working_days
            targeted_monthly_cost = csv_file.employee_cost_target * total_estimated_call

            no_of_days_left = csv_file.working_days - csv_file.completed_days
            call_attenment = 100 - avg_cx 
            resolution_or_ticket = 100 - avg_non
            monthly_call_projection = daily_call_average * csv_file.working_days
            employee_cost_per_month = csv_file.average_cost_employee * number_of_employees * csv_file.working_hour_per_day

            first_cal = employee_cost_per_month / csv_file.working_days if csv_file.working_days != 0  else 0
            
            sec_cal = (csv_file.average_cost_per_Call * daily_call_average)*csv_file.completed_days
            thrd_cal = daily_call_average * csv_file.completed_days
            cost_per_call_till_date = (first_cal + sec_cal)/thrd_cal  if thrd_cal != 0  else 0
            
            cost_target_achieve = (cost_per_call_till_date - csv_file.employee_cost_target)/csv_file.employee_cost_target if csv_file.employee_cost_target != 0 else 0
            cost_target_achieve = -cost_target_achieve* 100

            report1["working_hours_aligned_with_required_availability"] = working_hours_aligned_with_required_availability
            report1["actual_resource_working_hour"] = actual_resource_working_hour
            report1["overtime_hours_required"] = overtime_hours_required
            report1["no_of_resource_required"] = no_of_resource_required
            report1["process_and_technology_driven"] = process_and_technology_driven
            report1["total_estimated_call"] = total_estimated_call
            report1["targeted_monthly_cost"] = targeted_monthly_cost
            report1["call_handle_process"] = csv_file.call_handle_process
            report1["technology"] = csv_file.technology
            report1["average_call_per_day"] = csv_file.average_call_per_day

            report2["working_days_per_week"] = csv_file.working_days_per_week
            report2["cost_target"] = csv_file.employee_cost_target
            report2["average_cost_employee"] = csv_file.average_cost_employee
            report2["working_days"] = csv_file.working_days
            report2["working_hour_per_day"] = csv_file.working_hour_per_day
            report2["completed_days"] = csv_file.completed_days
            report2["average_cost_per_Call"] = csv_file.average_cost_per_Call
            report2["no_of_days_left"] = no_of_days_left
            report2["number_of_employee"] = number_of_employees
            report2["required_availability"] = csv_file.required_availability
            report2["call_attenment"] = call_attenment
            report2["resolution_or_ticket"] = resolution_or_ticket
            report2["daily_call_average"] = daily_call_average
            report2["monthly_call_projection"] = monthly_call_projection
            report2["employee_cost_per_month"] = employee_cost_per_month
            report2["cost_target_achieve"] = cost_target_achieve
            report2["cost_per_call_till_date"] = cost_per_call_till_date
            report2["employee_availability"] = employee_availability

            log = CsvLogDetails.objects.filter(
                uploaded_file__id=pk,
            ).values("center_name").annotate(
                varriation_in_resolution=Max("non_resloution") - Min("non_resloution"),
                varriation_in_cx=Max("cx_call_no_response") - Min("cx_call_no_response")
            ).values("center_name", "varriation_in_resolution", "varriation_in_cx")
            response_dict["report1"]    = report1
            response_dict["report2"]    = report2
            response_dict["report3"]    = log
        elif csv_file.modules.module_identifier == 12:
            report1 = {}
            report2 = {}
            report3 = {}
            report4 = {}
            total_impression = CsvLogDetails.objects.filter(
                uploaded_file__id=pk,
            ).aggregate(tot=Sum("total_impression_per_hour"))
            total_impression = total_impression.get("tot") if total_impression else 0
            avg_availability = CsvLogDetails.objects.filter(
                uploaded_file__id=pk,
            ).aggregate(avg=Avg("employee_availability"))
            employee_availability = avg_availability.get("avg") if avg_availability else 0
            avg_conversion = CsvLogDetails.objects.filter(
                uploaded_file__id=pk,
            ).aggregate(avg=Avg("conversion_rate"))
            number_of_employees = CsvLogDetails.objects.filter(
                uploaded_file__id=pk,
            ).count()

            avg_conversion = avg_conversion.get("avg") if avg_conversion else 0
            avg_conversion = avg_conversion / 100
            employee_availability = employee_availability / 100
            average_daily_impression = (total_impression * employee_availability * avg_conversion) / csv_file.completed_days if csv_file.completed_days !=0  else 0

            impression_target_based_on_daily_avg = average_daily_impression * csv_file.working_days
            accumulated_cost_of_impression_drop = csv_file.completed_days * impression_target_based_on_daily_avg

            no_of_days_left = csv_file.working_days - csv_file.completed_days
            impression_target_acheved = csv_file.online_impression_target - accumulated_cost_of_impression_drop
            remaining_impression_target = impression_target_acheved / no_of_days_left if no_of_days_left != 0 else 0 
            remaining_impression_expenditure = remaining_impression_target * csv_file.average_rate_per_impression
            
            impression_cost_till_date = csv_file.average_rate_per_impression * average_daily_impression * csv_file.completed_days
            impression_costing = impression_target_based_on_daily_avg * csv_file.average_rate_per_impression
            target_achieve = impression_target_based_on_daily_avg / csv_file.online_impression_target if csv_file.online_impression_target != 0 else 0

            working_hours_aligned_with_required_availability = number_of_employees * csv_file.working_hour_per_day * csv_file.working_days_per_week
            actual_resource_working_hour = number_of_employees * csv_file.working_hour_per_day * csv_file.working_days_per_week * employee_availability
            overtime_hour_required = working_hours_aligned_with_required_availability - actual_resource_working_hour

            no_of_resource_required = overtime_hour_required / (csv_file.working_days_per_week * csv_file.working_hour_per_day)

            weekly_overtime = csv_file.working_hour_per_day * csv_file.working_days_per_week * employee_availability
             
            report1["accumulated_cost_of_impression"] = accumulated_cost_of_impression_drop
            report1["impression_target_acheved"] = impression_target_acheved
            report1["remaining_impression_target"] = remaining_impression_target
            report1["remaining_impression_expenditure"] = remaining_impression_expenditure

            report2["working_hours_aligned_with_required_availability"] = working_hours_aligned_with_required_availability
            report2["actual_resource_working_hour"] = actual_resource_working_hour
            report2["overtime_hour_required"] = overtime_hour_required
            report2["no_of_resource_required"] = no_of_resource_required
            report2["working_days_in_week"] = csv_file.working_days_per_week

            report3["completed_days"] = csv_file.completed_days
            report3["working_days"] = csv_file.working_days
            report3["no_of_days_left"] = no_of_days_left
            report3["number_of_employees"] = number_of_employees
            report3["required_availability"] = csv_file.required_availability
            report3["working_hour_per_day"] = csv_file.working_hour_per_day
            report3["online_impression_target"] = csv_file.online_impression_target
            report3["average_daily_impression"] = average_daily_impression
            report3["average_impression_target"] = impression_target_based_on_daily_avg
            report3["average_rate_per_impression"] = csv_file.average_rate_per_impression
            report3["impression_cost_till_date"] = impression_cost_till_date
            report3["impression_costing"] = impression_costing
            report3["target_achieve"] = target_achieve
            report3["actual_working_hour"] = working_hours_aligned_with_required_availability
            report3["actual_resource_working_hour"] = actual_resource_working_hour
            report3["overtime_hour_required"] = overtime_hour_required
            report3["no_of_resource_required"] = no_of_resource_required
            report3["weekly_overtime"] = weekly_overtime
            report3["employee_availability"] = avg_availability.get("avg") if avg_availability else 0

            log = CsvLogDetails.objects.filter(
                uploaded_file__id=pk,
            ).values("center_name").annotate(
                total_conversion_rate=Avg("conversion_rate"),
                total_impression_drop=Avg("impression_drop"),
            ).values("center_name", "total_conversion_rate", "total_impression_drop")


            response_dict["report1"]    = report1
            response_dict["report2"]    = report2
            response_dict["report3"]    = report3
            response_dict["report4"]    = log

        response_dict["status"] = True
        return Response(response_dict, status=status.HTTP_200_OK)

class GetDepartment(APIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (CustomTokenAuthentication,)
    def get(self, request, pk):
        response_dict={"status":False}

        csv_file = UploadedCsvFiles.objects.filter(
            id=pk
        ).first()

        if csv_file.modules.module_identifier == 8:
            department_dict = []
            department = list(set(CsvLogDetails.objects.filter(uploaded_file__id=pk).values_list("department", flat=True)))
            for dep in department:
                department_dict.append(
                    {
                        "name":dep,
                    }
                )

            response_dict["department"] = department_dict
        
        elif csv_file.modules.module_identifier == 5:
            total_countries = []
            countries = list(set(CsvLogDetails.objects.filter(uploaded_file__id=pk).values_list("region", flat=True)))
            for i in countries:
                department_dict = []
                total_countries.append(
                    {
                        "name":i,
                        "department":department_dict,
                    }
                )
                department = list(set(CsvLogDetails.objects.filter(uploaded_file__id=pk, region=i).values_list("department", flat=True)))
                for dep in department:
                    designation_dict = []
                    department_dict.append(
                        {
                            "name":dep,
                            "designation":designation_dict,
                        }
                    )
                    designation = list(set(CsvLogDetails.objects.filter(uploaded_file__id=pk, region=i, department=dep).values_list("designation", flat=True)))
        
                    for des in designation:
                        exp_dict = []
                        designation_dict.append(
                            {
                                "name":des,
                                "experience":list(set(CsvLogDetails.objects.filter(uploaded_file__id=pk, designation=des, region=i, department=dep).values_list("experience", flat=True))),
                            }
                        )
            response_dict["countries"] = total_countries
        else:
            departments = list(set(CsvLogDetails.objects.filter(uploaded_file__id=pk).values_list("department", flat=True)))
            departments_dict = []
            for i in departments:
                if csv_file.modules.module_identifier == 3:
                    if DepartmentWeightage.objects.filter(
                        uploaded_file=csv_file,
                        department=i
                    ):
                        dep = DepartmentWeightage.objects.filter(
                            uploaded_file=csv_file,
                            department=i
                        ).last()
                        departments_dict.append(
                            {
                                "department":i,
                                "team":[],
                                "id":dep.id
                            }
                        )
                    else:
                        dep = DepartmentWeightage.objects.create(
                            uploaded_file=csv_file,
                            department=i
                        )
                        departments_dict.append(
                            {
                                "department":i,
                                "team":[],
                                "id":dep.id
                            }
                        )
                else:
                    team_list = list(set(CsvLogDetails.objects.filter(
                    uploaded_file__id=pk, department=i).values_list("team", flat=True)))
                    departments_dict.append(
                        {
                            "department":i,
                            "team":team_list
                        }
                    )
            response_dict["departments"] = departments_dict
        response_dict["status"] = True
        return Response(response_dict, status=status.HTTP_200_OK)


class GetTeam(APIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (CustomTokenAuthentication,)
    def get(self, request, pk):
        response_dict={"status":False}
        select_department = request.GET.get("department")
        team = list(set(CsvLogDetails.objects.filter(
            uploaded_file__id=pk, department=select_department).values_list("team", flat=True)))
        response_dict["team"] = team
        response_dict["status"] = True
        return Response(response_dict, status=status.HTTP_200_OK)


class AdminModules(APIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (CustomTokenAuthentication,)
    def get(self, request):
        response_dict={"status":False}
        logined_user =  request.user
        current_date = timezone.now().date()
        free_subscribed_modules = FreeSubscriptionDetails.objects.filter(
            user=request.user,
            free_subscription_end_date__gte=current_date
        )
        Subscribed_modules = SubscriptionDetails.objects.filter(user=request.user,).last()
        if logined_user.user_type == 'ADMIN':
            if Subscribed_modules:
                free_subscribed_modules_ids = []
                for i in free_subscribed_modules:
                    if i.module.all():
                        free_subscribed_modules_ids.extend(
                            list(i.module.all().values_list("id", flat=True))
                        )
                all_modules = ModuleDetails.objects.filter(
                    Q(id__in=Subscribed_modules.module.all().values_list("id", flat=True))|
                    Q(id__in=free_subscribed_modules_ids)
                )
                invited_users = InviteDetails.objects.filter(user=logined_user, is_deleted=False, is_verified=False, is_reject=False)
                
                response_dict["user"] = {
                    "id": logined_user.id,
                    "first_name": logined_user.first_name,
                    "last_name": logined_user.last_name,
                    "email": logined_user.email,
                
                }
                total_users = logined_user.available_free_users + logined_user.available_paid_users
                response_dict["available_users"] = total_users
                response_dict["status"] = True
                response_dict["modules"] = ModuleDetailsSerializer(all_modules, context={'request':request}, many=True).data
                response_dict["additional_users"] = self.get_users_with_password()
                response_dict["invited_users"] = InvitedUserSerializer(invited_users, context={'request':request}, many=True).data
                return Response(response_dict, status=status.HTTP_200_OK)
            elif free_subscribed_modules:
                free_subscribed_modules_ids = []
                invited_users = InviteDetails.objects.filter(user=logined_user, is_deleted=False, is_verified=False)
                for i in free_subscribed_modules:
                    if i.module.all():
                        free_subscribed_modules_ids.extend(
                            list(i.module.all().values_list("id", flat=True))
                        )
                free_modules = ModuleDetails.objects.filter(id__in=free_subscribed_modules_ids).order_by("module_identifier")
                response_dict["modules"] = ModuleDetailsSerializer(free_modules, context={'request':request}, many=True).data
                response_dict["additional_users"] = self.get_users_with_password()
                response_dict["invited_users"] = InvitedUserSerializer(invited_users, context={'request':request}, many=True).data
                response_dict["status"] = True
                return Response(response_dict, status=status.HTTP_200_OK)
            else:
                response_dict["modules"] = []
                response_dict["additional_users"] = []
                response_dict["invited_users"] = []
                response_dict["status"] = True
                return Response(response_dict, status=status.HTTP_200_OK)
        else:
            response_dict["error"] = "Access denied, Only Admin can access the module list"
            return Response(response_dict, status=status.HTTP_400_BAD_REQUEST)
    

    def get_users_with_password(self):
        users_with_password = UserProfile.objects.filter(user_type="USER", is_active=True).exclude(password="")
        admin_id = self.request.user.id
        users_with_password = users_with_password.filter(created_admin=admin_id)
        serializer = UserSerializer(users_with_password, many=True)
        return serializer.data

    def get_users_without_password(self):
        users_without_password = UserProfile.objects.filter(user_type="USER", is_active=True, password="")
        admin_id = self.request.user.id
        users_without_password = users_without_password.filter(created_admin=admin_id)
        serializer = UserSerializer(users_without_password, many=True)
        return serializer.data
        
    
            
class UserInviteModule(APIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (CustomTokenAuthentication,)

    def post(self, request):
        response_dict = {"status": False}
        admin_login =  request.user

        if admin_login.user_type == 'ADMIN':
            data = request.data
            serializer = UserInviteSerializer(data=data)

            user_exists = UserProfile.objects.filter(email=data.get("email")).exists()
            deleted_user = UserProfile.objects.filter(email=data.get("email"), is_active=False).first()
            existing_invite = InviteDetails.objects.filter(email=data.get("email")).last()

            if user_exists and not deleted_user:
                response_dict["error"] = "User already exists"
                return Response(response_dict, status=status.HTTP_200_OK)
            
            if existing_invite and not existing_invite.is_verified and not existing_invite.is_reject:
                response_dict["error"] = "User already invited, but no action has been taken"
                return Response(response_dict, status=status.HTTP_403_FORBIDDEN)

                
            available_free_user = admin_login.available_free_users
            available_paid_user = admin_login.available_paid_users

            selected_modules = data.get("selected_modules")
            selected_bundles = data.get("selected_bundles")
            assigned_module_names = []

            if available_free_user>0:
                
                if deleted_user:
                    if deleted_user and deleted_user.is_free_user == True:
                        
                        if selected_modules:
                            existing_assign_delete_user = UserAssignedModules.objects.filter(user=deleted_user).first()
                            if existing_assign_delete_user:
                                existing_assign_delete_user.module.clear()
                                for module_id in selected_modules:
                                    try:
                                        module = ModuleDetails.objects.get(id=module_id)
                                    except ModuleDetails.DoesNotExist:
                                        response_dict["error"] = f"Module with ID {module_id} doesn't exist"
                                        return Response(response_dict, status=status.HTTP_400_BAD_REQUEST)

                                    existing_assign_delete_user.module.add(module)
                                    assigned_module_names.append(module.title)
                            else:  
                                existing_assign_delete_user = UserAssignedModules.objects.create(user=deleted_user)
                                for module_id in selected_modules:
                                    try:
                                        module = ModuleDetails.objects.get(id=module_id)
                                    except ModuleDetails.DoesNotExist:
                                        response_dict["error"] = f"Module with ID {module_id} doesn't exist"
                                        return Response(response_dict, status=status.HTTP_400_BAD_REQUEST)

                                    existing_assign_delete_user.module.add(module)
                                    assigned_module_names.append(module.title)
                            
                        else:
                            response_dict["error"] = "No module selected"
                        deleted_user.is_active = True
                        deleted_user.save()
                        admin_login.available_free_users -= 1
                        admin_login.save()
                        response_dict["status"] = True
                        response_dict['message'] = "Reinvited the deleteed user"
                    else:
                        if selected_modules:
                            existing_assign_delete_user = UserAssignedModules.objects.filter(user=deleted_user).first()
                            if existing_assign_delete_user:
                                existing_assign_delete_user.module.clear()
                                for module_id in selected_modules:
                                    try:
                                        module = ModuleDetails.objects.get(id=module_id)
                                    except ModuleDetails.DoesNotExist:
                                        response_dict["error"] = f"Module with ID {module_id} doesn't exist"
                                        return Response(response_dict, status=status.HTTP_400_BAD_REQUEST)

                                    existing_assign_delete_user.module.add(module)
                                    assigned_module_names.append(module.title)
                            else:  
                                existing_assign_delete_user = UserAssignedModules.objects.create(user=deleted_user)
                                for module_id in selected_modules:
                                    try:
                                        module = ModuleDetails.objects.get(id=module_id)
                                    except ModuleDetails.DoesNotExist:
                                        response_dict["error"] = f"Module with ID {module_id} doesn't exist"
                                        return Response(response_dict, status=status.HTTP_400_BAD_REQUEST)

                                    existing_assign_delete_user.module.add(module)
                                    assigned_module_names.append(module.title)
                        else:
                            response_dict["error"] = "No module selected"
                        deleted_user.is_active = True
                        deleted_user.save()
                        admin_login.available_paid_users -= 1
                        admin_login.save()
                        response_dict["status"] = True
                        response_dict['message'] = "Reinvited the deleteed user"  
                        return Response(response_dict, status=status.HTTP_200_OK)

                elif not deleted_user:
                    invite_details = InviteDetails.objects.create(
                        email=data.get("email"),
                        name=data.get("first_name"),
                        user=request.user,
                        is_free_user=True
                    )             

                    admin_login.available_free_users -= 1
                    admin_login.save()

                    
                    if selected_modules:
                        for module_id in selected_modules:
                            
                            try:
                                module = ModuleDetails.objects.get(id=module_id)
                                invite_details.module.add(module)
                                assigned_module_names.append(module.title)
                            except ModuleDetails.DoesNotExist:
                                response_dict["error"] = f"Module with ID {module_id} doesn't exist"
                                return Response(response_dict, status=status.HTTP_400_BAD_REQUEST)

                    if selected_bundles:
                        for bundle_id in selected_bundles:
                            try:
                                bundle = ModuleDetails.objects.get(id=bundle_id)
                                invite_details.bundle.add(bundle)
                                assigned_module_names.append(bundle.title)
                            except ModuleDetails.DoesNotExist:
                                response_dict["error"] = f"Module with ID {bundle_id} doesn't exist"
                                return Response(response_dict, status=status.HTTP_400_BAD_REQUEST)


                    # send otp to mail
                    email = request.data.get('email')
                    mail_subject = 'Invitation Link'
                    current_domain = request.get_host()

                    html_message = render_to_string('invitation_link.html', {
                        'invited_user_name': data.get('first_name'),
                        'invitation_link': f'http://{current_domain}/accept-reject/{invite_details.id}/',
                        'invited_by':request.user
                    })
                    email = EmailMessage("Invitation Link", html_message, to=[email])
                    email.content_subtype = "html"
                    email.send() 

                    response_dict["status"] = True
                    response_dict["message"] = "Invite Link Send to mail"
                    return Response(response_dict, status=status.HTTP_200_OK)
                    
                else:
                    response_dict["error"] = "Not a user"
            elif available_paid_user>0:
                if available_paid_user:  
                    invite_details = InviteDetails.objects.create(
                        email=data.get("email"),
                        name=data.get("first_name"),
                        user = request.user,
                        is_free_user=False
                    )

                    admin_login.available_paid_users -= 1
                    admin_login.save()

                    # assign module
                    if selected_modules:
                    
                        for module_id in selected_modules:
                        
                            try:
                                module = ModuleDetails.objects.get(id=module_id)
                                invite_details.module.add(module)
                                assigned_module_names.append(module.title)
                            except ModuleDetails.DoesNotExist:
                                response_dict["error"] = f"Module with ID {module_id} doesn't exist"
                                return Response(response_dict, status=status.HTTP_400_BAD_REQUEST)

                    if selected_bundles:
                        for bundle_id in selected_bundles:
                            try:
                                bundle = ModuleDetails.objects.get(id=bundle_id)
                                invite_details.bundle.add(bundle)
                                assigned_module_names.append(bundle.title)
                            except ModuleDetails.DoesNotExist:
                                response_dict["error"] = f"Module with ID {bundle_id} doesn't exist"
                                return Response(response_dict, status=status.HTTP_400_BAD_REQUEST)

                    # send otp to mail
                    email = request.data.get('email')
                    mail_subject = 'Invitation Link'
                    current_domain = request.get_host()

                    html_message = render_to_string('invitation_link.html', {
                        'invited_user_name': data.get('first_name'),
                        'invitation_link': f'http://{current_domain}/accept-reject/{invite_details.id}/',
                        'invited_by':request.user
                    })
                    email = EmailMessage("Invitation Link", html_message, to=[email])
                    email.content_subtype = "html"
                    email.send() 

                    response_dict["status"] = True
                    response_dict["message"] = "Invite Link Send to mail"
                    return Response(response_dict, status=status.HTTP_200_OK)
                else:
                    response_dict["error"] = "Not a user"  
                    return Response(response_dict, status=status.HTTP_200_OK)
                
            else:
                response_dict["error"] = "No paid or free users are available"  
                return Response(response_dict, status=status.HTTP_200_OK)

        else:
            response_dict["error"] = "Access denied, Only Admin can access the module list"
            return Response(response_dict, status=status.HTTP_400_BAD_REQUEST)
        return Response(response_dict, status=status.HTTP_200_OK)


class UnAssignUserlist(APIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (CustomTokenAuthentication,) 

    def get(self, request,pk):
        response_dict = {"status":True}
        user = request.user
        module = ModuleDetails.objects.get(id=pk)
        current_date = timezone.now().date()
        free_subscribed_modules = FreeSubscriptionDetails.objects.filter(
            user=request.user,
            free_subscription_end_date__gte=current_date,
            module__id=pk
        )
        
        if free_subscribed_modules:
            un_assigned_user = UserProfile.objects.filter(created_admin=user).exclude(userassignedmodules__module=module)  
            response_dict["module"] = module.title
            response_dict["un_assigned_users"] = UserSerializer(un_assigned_user, context={"request":request}, many=True).data

        else:
            subscribed_modules = SubscriptionDetails.objects.filter(user=request.user, module=pk).exists()
            if subscribed_modules:
                un_assigned_user = UserProfile.objects.filter(created_admin=user).exclude(userassignedmodules__module=module)  
                # unassigned_user = un_assigned_user.filter(created_admin=user)
                response_dict["module"] = module.title
                response_dict["un_assigned_users"] = UserSerializer(un_assigned_user, context={"request":request}, many=True).data
            else:
                response_dict["error"] = "User is not subscribed the module"
        return Response(response_dict, status=status.HTTP_200_OK)

   
class AssignUser(APIView):
    permission_classes =(IsAuthenticated,)
    authentication_classes = (CustomTokenAuthentication,) 

    def post(self, request, pk):
        response_dict = {"status":False}
        user = request.user
        if user.user_type == "ADMIN":
            try:
                module = ModuleDetails.objects.get(id=pk)
            except ModuleDetails.DoesNotExist:
                response_dict["error"] = f"Module with ID {pk} does not exists"
                return Response(response_dict, status=status.HTTP_200_OK)
            users_to_assign = request.data.get("user_ids", [])
            
            for user_id in users_to_assign:
                try:
                    user_profile = UserProfile.objects.get(id=user_id)

                except UserProfile.DoesNotExist:
                    response_dict["error"] = f"User with the ID {user_id} does not exsts"
                    return Response(response_dict, status=status.HTTP_403_FORBIDDEN)
                
                current_date = timezone.now().date()
                free_subscribed_modules = FreeSubscriptionDetails.objects.filter(
                    user=request.user,
                    free_subscription_end_date__gte=current_date,
                    module__id=pk
                )
                subscribed_module = SubscriptionDetails.objects.filter(subscription_end_date__gte=current_date, user=request.user, module=pk).exists()
                
                if subscribed_module:
                    if UserAssignedModules.objects.filter(user=user_profile).exists():
                        if UserAssignedModules.objects.filter(user=user_profile, module=module).exists():
                            response_dict["error"] = f"User {user_profile.id} is already assigned to module {module.id}"
                        else:
                            user_assign_object = UserAssignedModules.objects.filter(user=user_profile).first()
                            user_assign_object.module.add(module)
                            response_dict["message"] = "User is assigned to the module"
                    else:
                        assign_user = UserAssignedModules.objects.create(user=user_profile)
                        assign_user.module.add(module)
                        response_dict["satatus"] = True
                        response_dict["message"] = f"User is added to the module"
                elif free_subscribed_modules:
                    if UserAssignedModules.objects.filter(user=user_profile).exists():
                        if UserAssignedModules.objects.filter(user=user_profile, module=module).exists():
                            response_dict["error"] = f"User {user_profile.id} is already assigned to module {module.id}"
                        else:
                            user_assign_object = UserAssignedModules.objects.filter(user=user_profile).first()
                            user_assign_object.module.add(module)
                            response_dict["message"] = "User is assigned to the module"
                    else:
                        assign_user = UserAssignedModules.objects.create(user=user_profile)
                        assign_user.module.add(module)
                        response_dict["satatus"] = True
                        response_dict["message"] = f"User is added to the module"
                else:
                    response_dict["error"] = "Not subscribed the module"
            
            return Response(response_dict, status=status.HTTP_200_OK)
        else:
            response_dict["error"] = "Access denied, Only Admin can access the module list"
            return Response(response_dict, status=status.HTTP_403_FORBIDDEN)
    

class UserModuleList(APIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (CustomTokenAuthentication,)

    def get(self, request, pk):
        response_dict = {"status": True}
        current_date = timezone.now().date()
        user_obj = UserAssignedModules.objects.filter(user__id=pk, module__isnull=False).last()
        total_c = 0
        module_ids = []
        subscription = SubscriptionDetails.objects.filter(
            user=request.user, 
            is_subscribed=True,
            subscription_end_date__gte=current_date
        ).order_by("-id").first()
        if subscription:
            module_ids = list(subscription.module.all().values_list("id", flat=True))
            total_c = total_c + len(module_ids)

        free_subscribed_modules = FreeSubscriptionDetails.objects.filter(
            user=request.user,
            free_subscription_end_date__gte=current_date,
        )
        free_subscribed_modules_ids = []
        for i in free_subscribed_modules:
            if i.module.all():
                free_subscribed_modules_ids.extend(
                    list(i.module.exclude(id__in=module_ids).values_list("id", flat=True))
                )
        total_c = total_c + len(free_subscribed_modules_ids)
        response_dict["total_modules"] = total_c
        if user_obj:
            serializer = UserAssignedModuleSerializers(user_obj)
            response_dict["status"] = True
            response_dict["modules"] = serializer.data
        else:
            response_dict["error"] = f"User with ID {pk} has no assigned modules"
        return Response(response_dict, status=status.HTTP_200_OK)
    

class DeleteModule(APIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (CustomTokenAuthentication, )

    def post(self, request,user_id, module_id,):
        response_dict = {"status": False}

        try :
            user_to_delete = UserAssignedModules.objects.filter(user__id=user_id).last()
            module_to_delete = ModuleDetails.objects.get(id=module_id)
        except UserAssignedModules.DoesNotExist:
            response_dict["error"] = f"User with the id  does not exists"
            return Response(response_dict, status=status.HTTP_400_BAD_REQUEST)
        except ModuleDetails.DoesNotExist:
            response_dict["error"] = f"Module with the id  does not exists"
            return Response(response_dict, status=status.HTTP_400_BAD_REQUEST)
        
        if not user_to_delete.module.filter(id=module_id).exists():
            response_dict["error"] = "User is not associated with the specified module"
            return Response(response_dict, status=status.HTTP_400_BAD_REQUEST)
        
        user_to_delete.module.remove(module_to_delete)

        response_dict["message"] = "Successfully deleted the Module from the User"
        response_dict["status"] = True
        return Response(response_dict, status=status.HTTP_200_OK)


class UnassignedModule(APIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (CustomTokenAuthentication,)

    def get(self, request, pk):
        response_dict = {"status":True}
        current_date = timezone.now().date()
        free_subscribed_modules = FreeSubscriptionDetails.objects.filter(
            user=request.user,
            free_subscription_end_date__gte=current_date,
        )
        free_subscribed_modules_ids = []
        for i in free_subscribed_modules:
            if i.module.all():
                free_subscribed_modules_ids.extend(
                    list(i.module.all().values_list("id", flat=True))
                )
        try:
            user_obj = UserProfile.objects.get(id=pk, )
        except UserProfile.DoesNotExist:
            response_dict["error"] = f"User with the ID {pk} does not exists"
            return Response(response_dict, status=status.HTTP_400_BAD_REQUEST)
        
        if SubscriptionDetails.objects.filter(user=user_obj.created_admin).exists():
            subscribtion = SubscriptionDetails.objects.filter(user=user_obj.created_admin).first()
            subscribed_modules = subscribtion.module.all()
            unassigned_modules = ModuleDetails.objects.filter(
                Q(id__in=free_subscribed_modules_ids)|
                Q(id__in=subscribed_modules.values_list("id", flat=True))
            ).exclude(userassignedmodules__user=user_obj)
            available_un_assiged_module = unassigned_modules
            response_dict["unassigned module"] = ModuleDetailsSerializer(available_un_assiged_module, context={"request":request}, many=True).data
        elif user_obj.created_admin.free_subscribed == True:
            unassigned_modules = ModuleDetails.objects.filter(id__in=free_subscribed_modules_ids).exclude(userassignedmodules__user=user_obj)
            response_dict["unassigned module"] = ModuleDetailsSerializer(unassigned_modules, context={"request":request}, many=True).data
        else:
            response_dict["message"] = f"Admin  not have subscription"
        return Response(response_dict, status=status.HTTP_200_OK)


class AssignModulesToUser(APIView):
    permission_classes =(IsAuthenticated,)
    authentication_classes = (CustomTokenAuthentication,) 

    def post(self, request, pk):
        response_dict = {"status":True}
        serializer = ModuleSToUserserializer(data=request.data)
        
        if request.user.user_type == "ADMIN":
            try:
                assign_user = UserProfile.objects.get(id=pk)
            except UserProfile.DoesNotExist:
                response_dict["error"] = f"User with ID {pk} does not exists"
                return Response(response_dict, status=status.HTTP_404_NOT_FOUND)
            
            serializer.is_valid(raise_exception=True)

            module_to_assign = serializer.validated_data.get('module_ids',[])  

            for module_id in module_to_assign:
                try:
                    module = ModuleDetails.objects.get(id=module_id)

                except ModuleDetails.DoesNotExist:
                    response_dict["error"] = f"Module with the ID {module_id} does not exsts"

                if UserAssignedModules.objects.filter(user=assign_user).exists():
                    user_assign_object = UserAssignedModules.objects.filter(user=assign_user).first()
                    user_assign_object.module.add(module)
                    response_dict["message"] = "Mdule assigned for the user"
                else:
                    assigned_user = UserAssignedModules.objects.create(user=assign_user)
                    assigned_user.module.add(module)
                    response_dict["message"] = f"User with ID {assign_user.id} added to the module id{module.id}"
        else:
            response_dict["error"] = "Access denied, Only Admin can access the module list"
            return Response(response_dict, status=status.HTTP_403_FORBIDDEN)

        return Response(response_dict, status=status.HTTP_200_OK)


class PermanentDeleteUserFromAdmin(APIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (CustomTokenAuthentication,)

    def post(self, request, pk):
    
        response_dict = {"status": False}
        admin_user = request.user

        try:
            deleted_user = UserProfile.objects.get(id=pk, created_admin=admin_user, is_active=True)
        except UserProfile.DoesNotExist:
            return Response({"message": "User not found or access denied", "status": False}, status=status.HTTP_404_NOT_FOUND) 


        try:
            deleted_user_module = UserAssignedModules.objects.get(user=deleted_user)
        except UserAssignedModules.DoesNotExist:
            deleted_user_module = None

        
        if deleted_user_module:
            # Get all modules assigned to the user
            modules_assigned = list(deleted_user_module.module.all())

            # Create a DeleteUsersLog entry and associate all modules with it
            delete_user_log_entry = DeleteUsersLog.objects.create(
                user=deleted_user,
                deleted_by=admin_user,
                is_active=True, 
            )
            delete_user_log_entry.module.set(modules_assigned)  # Associate all modules

            # Remove all modules from the UserAssignedModules
            deleted_user_module.module.clear()
        else:
            modules_assigned = []

        if deleted_user:
            deleted_user.is_active = False
            deleted_user.save()
            if deleted_user.is_free_user:
                admin_user.available_free_users += 1
                admin_user.save()
            else: 
                admin_user.available_paid_users += 1
                admin_user.save()
            response_dict["message"] = "Permanently marked the user as deleted and deleted all assigned modules."
            response_dict["status"] = True
        else:
            response_dict["message"] = "Already Deleted"
            response_dict["status"] = True

        return Response(response_dict, status=status.HTTP_200_OK)


class CartHome(APIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (CustomTokenAuthentication,)

    def get(self, request):

        response_dict = {"status":True}
        admin_user = request.user

        subscribed_module = SubscriptionDetails.objects.filter(user=admin_user)
        module_count = subscribed_module.aggregate(total_modules=Count('module'))
        total_user_count = int(admin_user.available_free_users) + int(admin_user.available_paid_users) 

        users_with_password_count = UserProfile.objects.filter(created_admin=admin_user).exclude(password='').count()

        response_dict["subscribed_module"] = SubscriptionModuleSerilzer(subscribed_module, context={'request':request}, many=True).data
        response_dict["module_count"] = module_count['total_modules']
        response_dict["total_user_count"] = total_user_count
        response_dict["assigned_users"] = users_with_password_count
        return Response(response_dict, status=status.HTTP_200_OK)
    

class UserPurchasePrice(APIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (CustomTokenAuthentication,)

    def get(self, request):
       
        response_dict = {"status":True}
        admin_user = request.user

        admin_subscription = SubscriptionDetails.objects.filter(user=admin_user, is_subscribed=True).first()

        if admin_subscription is None:
            return Response({"error": "Admin subscription not found"}, status=status.HTTP_404_NOT_FOUND)

        if not hasattr(admin_subscription, 'subscription_end_date'):
            return Response({"error": "Admin subscription doesn't have a subscription_end_date"}, status=status.HTTP_400_BAD_REQUEST)

        
        subscription_end_date = admin_subscription.subscription_end_date
        current_date = datetime.now().date()
        remaining_days = (subscription_end_date - current_date).days

        subscription_type = admin_subscription.subscription_type

        response_dict["Subscription_type"] = subscription_type

        weekly_price = 4
        monthly_price = 14
        yearly_price = 160

        if subscription_type == "WEEK":
            amount = (weekly_price / 7) * remaining_days
        elif subscription_type == "MONTH":
            amount = (monthly_price / 30) * remaining_days
        elif subscription_type == "YEAR":
            amount = (yearly_price / 365) * remaining_days
        else:
            return Response({"error": "Invalid purchase duration"}, status=status.HTTP_400_BAD_REQUEST)
        
        

        price_data = {
            "added_by": {"id": admin_user.id}, 
            "amount": amount, 
        }

        response_dict["price_data"] = price_data
        response_dict["subscription_end_date"] = subscription_end_date
        return Response(response_dict, status=status.HTTP_200_OK)
    

class UserPurchasePriceV2(APIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (CustomTokenAuthentication,)

    def get(self, request):
        subscription_type = request.GET.get("subscription_type")
        total_count = int(request.GET.get("total_count", 1))
        action_type = request.GET.get("action_type")
        response_dict = {"status":True}
        admin_user = request.user
        current_date = datetime.now().date()
        admin_subscription = UserSubscriptionDetails.objects.filter(user=admin_user).first()
        
        if action_type == "renew":            
            subscription_type = admin_subscription.subscription_type
            total_count = admin_subscription.user_count
            weekly_price = 4
            monthly_price = 14
            yearly_price = 160
            if subscription_type == "WEEK":
                if admin_subscription.subscription_end_date < current_date:
                    subscription_end_date = current_date
                else:
                    subscription_end_date = admin_subscription.subscription_end_date
                new_end_date = subscription_end_date + timedelta(days=7)
                remaining_days = (new_end_date - subscription_end_date).days
                amount = (weekly_price / 7) * remaining_days
                amount = amount * total_count
                subscription_end_date = new_end_date
                
            elif subscription_type == "MONTH":
                if admin_subscription.subscription_end_date < current_date:
                    subscription_end_date = current_date
                else:
                    subscription_end_date = admin_subscription.subscription_end_date
                new_end_date = subscription_end_date + timedelta(days=30)
                remaining_days = (new_end_date - subscription_end_date).days
                amount = (monthly_price / 30) * remaining_days
                amount = amount * total_count
                subscription_end_date = new_end_date
            elif subscription_type == "YEAR":
                if admin_subscription.subscription_end_date < current_date:
                    subscription_end_date = current_date
                else:
                    subscription_end_date = admin_subscription.subscription_end_date
                new_end_date = subscription_end_date + timedelta(days=365)
                remaining_days = (new_end_date - subscription_end_date).days
                amount = (yearly_price / 365) * remaining_days
                amount = amount * total_count
                subscription_end_date = new_end_date
            else:
                return Response({"error": "Invalid purchase duration"}, status=status.HTTP_400_BAD_REQUEST)
        elif action_type == "count_upgrade":
            subscription_end_date = admin_subscription.subscription_end_date
            if admin_subscription.subscription_type == "WEEK":
                pending = (subscription_end_date - current_date).days
                pending_amount = (4 / 7) * pending
                user_count = admin_subscription.user_count
                total_count = total_count - user_count
                amount = total_count * pending_amount
            elif subscription_type == "MONTH":
                pending = (subscription_end_date - current_date).days
                pending_amount = (14 / 30) * pending
                user_count = admin_subscription.user_count
                total_count = total_count - user_count
                amount = total_count * pending_amount
            elif subscription_type == "YEAR":
                pending = (subscription_end_date - current_date).days
                pending_amount = (160 / 365) * pending
                user_count = admin_subscription.user_count
                total_count = total_count - user_count
                amount = total_count * pending_amount

        elif action_type == "plan_upgrade":
            
            if admin_subscription.subscription_type == subscription_type:
                subscription_end_date = admin_subscription.subscription_end_date
                if subscription_type == "WEEK":
                    new_end_date = current_date + timedelta(days=7)
                    pending = (new_end_date - subscription_end_date).days
                    pending_amount = (4 / 7) * pending
                    amount = pending_amount * user_count

                elif subscription_type == "MONTH":
                    new_end_date = current_date + timedelta(days=30)
                    pending = (new_end_date - subscription_end_date).days
                    amount = (14 / 30) * pending

                elif subscription_type == "YEAR":
                    new_end_date = current_date + timedelta(days=365)
                    pending = (new_end_date - subscription_end_date).days
                    amount = (160 / 365) * pending
                subscription_end_date = new_end_date

            elif admin_subscription.subscription_type == "WEEK":
                if subscription_type == "MONTH":
                    user_count = admin_subscription.user_count
                    subscription_end_date = admin_subscription.subscription_end_date
                    new_end_date = current_date + timedelta(days=30)
                    pending = (new_end_date - subscription_end_date).days
                    pending_amount = (14 / 30) * pending
                    amount = pending_amount * user_count

                elif subscription_type == "YEAR":
                    user_count = admin_subscription.user_count
                    subscription_end_date = admin_subscription.subscription_end_date
                    new_end_date = current_date + timedelta(days=365)
                    pending = (new_end_date - subscription_end_date).days
                    pending_amount = (160 / 365) * pending
                    amount = pending_amount * user_count
                subscription_end_date = new_end_date
            elif admin_subscription.subscription_type == "MONTH":
                if subscription_type == "YEAR":
                    user_count = admin_subscription.user_count
                    subscription_end_date = admin_subscription.subscription_end_date
                    new_end_date = current_date + timedelta(days=365)
                    pending = (new_end_date - subscription_end_date).days
                    pending_amount = (160 / 365) * pending
                    pending_amount_t = pending_amount * user_count
                    total_c = total_count - user_count
                    actual_amount_t = 160 * total_c
                    amount = pending_amount_t + actual_amount_t
                subscription_end_date = new_end_date

        elif action_type == "both_upgrade":
            current_date = datetime.now().date()
            if admin_subscription.subscription_type == subscription_type:
                user_count = admin_subscription.user_count
                subscription_end_date = admin_subscription.subscription_end_date
                if subscription_type == "WEEK":
                    new_end_date = current_date + timedelta(days=7)
                    pending = (new_end_date - subscription_end_date).days
                    pending_amount = (4 / 7) * pending
                    pending_amount_t = pending_amount * user_count
                    total_c = total_count - user_count
                    actual_amount_t = 4 * total_c
                    amount = pending_amount_t + actual_amount_t

                elif subscription_type == "MONTH":
                    new_end_date = current_date + timedelta(days=30)
                    pending = (new_end_date - subscription_end_date).days
                    pending_amount = (14 / 30) * pending
                    pending_amount_t = pending_amount * user_count
                    total_c = total_count - user_count
                    actual_amount_t = 14 * total_c
                    amount = pending_amount_t + actual_amount_t

                elif subscription_type == "YEAR":
                    new_end_date = current_date + timedelta(days=365)
                    pending = (new_end_date - subscription_end_date).days
                    pending_amount = (160 / 365) * pending
                    pending_amount_t = pending_amount * user_count
                    total_c = total_count - user_count
                    actual_amount_t = 160 * total_c
                    amount = pending_amount_t + actual_amount_t

                subscription_end_date = new_end_date
            elif admin_subscription.subscription_type == "WEEK":
                if subscription_type == "MONTH":
                    user_count = admin_subscription.user_count
                    subscription_end_date = admin_subscription.subscription_end_date
                    new_end_date = current_date + timedelta(days=30)
                    pending = (new_end_date - subscription_end_date).days
                    pending_amount = (14 / 30) * pending
                    pending_amount_t = pending_amount * user_count
                    total_c = total_count - user_count
                    actual_amount_t = 14 * total_c
                    amount = pending_amount_t + actual_amount_t

                elif subscription_type == "YEAR":
                    user_count = admin_subscription.user_count
                    subscription_end_date = admin_subscription.subscription_end_date
                    new_end_date = current_date + timedelta(days=365)
                    pending = (new_end_date - subscription_end_date).days
                    pending_amount = (160 / 365) * pending
                    pending_amount_t = pending_amount * user_count
                    total_c = total_count - user_count
                    actual_amount_t = 160 * total_c
                    amount = pending_amount_t + actual_amount_t

                subscription_end_date = new_end_date
            
            elif admin_subscription.subscription_type == "MONTH":
                if subscription_type == "YEAR":
                    user_count = admin_subscription.user_count
                    subscription_end_date = admin_subscription.subscription_end_date
                    new_end_date = current_date + timedelta(days=365)
                    pending = (new_end_date - subscription_end_date).days
                    pending_amount = (160 / 365) * pending
                    pending_amount_t = pending_amount * user_count
                    total_c = total_count - user_count
                    actual_amount_t = 160 * total_c
                    amount = pending_amount_t + actual_amount_t

                subscription_end_date = new_end_date
        else:
            
            weekly_price = 4
            monthly_price = 14
            yearly_price = 160
            if subscription_type == "WEEK":
                amount = weekly_price * total_count
                subscription_end_date = current_date + timedelta(days=7)
            elif subscription_type == "MONTH":
                amount = monthly_price * total_count
                subscription_end_date = current_date + timedelta(days=30)
            elif subscription_type == "YEAR":
                amount = yearly_price * total_count
                subscription_end_date = current_date + timedelta(days=365)
            else:
                return Response({"error": "Invalid purchase duration"}, status=status.HTTP_400_BAD_REQUEST)

        price_data = {
            "added_by": {"id": admin_user.id}, 
            "amount": amount, 
        }

        response_dict["price_data"] = price_data
        response_dict["subscription_end_date"] = subscription_end_date
        return Response(response_dict, status=status.HTTP_200_OK)
    

class AddToCartView(APIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (CustomTokenAuthentication,)

    def post(self, request):
        response_dict = {'status':True}
        admin_user = request.user

        if admin_user.user_type == 'ADMIN':
            user_count = request.data.get('count')
            amount = request.data.get('amount')

            admin_subscription = SubscriptionDetails.objects.filter(user=admin_user).first()
            subscription_end_date = admin_subscription.subscription_end_date
            current_date = datetime.now().date()

            if subscription_end_date != current_date:

                if AddToCart.objects.filter(added_by=admin_user, is_active=True).exists():
                    cart_obj = AddToCart.objects.filter(added_by=admin_user).last()
                    cart_obj.count = cart_obj.count + user_count
                    cart_obj.amount = amount
                    cart_obj.save()
                    response_dict["message"] = "Update the User count"
                    return Response(response_dict, status=status.HTTP_200_OK)


                else:
                    AddToCart.objects.create(added_by=admin_user, count=user_count, amount=amount, is_active=True)
                    response_dict["message"] = "Users Added to cart"
                
                    return Response(response_dict, status=status.HTTP_200_OK)
            else:
                response_dict["error"] = "Your subscription Expired !"
                return Response(response_dict, status=status.HTTP_400_BAD_REQUEST)
        else:
            response_dict["error"] = "Access denied, Only Admin can access the module list"
            return Response(response_dict, status=status.HTTP_403_FORBIDDEN)
        

class ModulePurchaseHistory(APIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (CustomTokenAuthentication,)

    def get(self, request):
        admin_user = request.user
        response_dict = {'status': False}

        subscription_details =  PurchaseDetails.objects.filter(user=admin_user, status='Placed', is_active=True, parchase_user_type='Subscription')
        if admin_user.user_type == 'ADMIN':
            if subscription_details:
                subscription_details =  PurchaseDetails.objects.filter(user=admin_user, status='Placed', is_active=True, parchase_user_type='Subscription')
                response_dict = {'status': True}
                response_dict["subscription-details"] = PurchaseHistorySerializer(subscription_details, context={'request': request}, many=True).data
                # response_dict["module"] = module_data
                return Response(response_dict, status=status.HTTP_200_OK)
            else:
                response_dict["subscription-details"] = []
                return Response(response_dict, status=status.HTTP_200_OK)
        else:
            response_dict = {'status': False}
            response_dict["error"] = "Access denied, Only Admin can access the module list"
            return Response(response_dict, status=status.HTTP_403_FORBIDDEN)


class UserPurchaseHistory(APIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (CustomTokenAuthentication,)

    def get(self, request):
        admin_user = request.user
        response_dict = {'status': True}

        if admin_user.user_type == 'ADMIN':
            purchase_user_details = PurchaseDetails.objects.filter(user=admin_user, status='Placed', is_active=True, parchase_user_type='User')
            if purchase_user_details:
                response_dict["subscription-details"] = UserPurchaseHistorySerializer(purchase_user_details, context={'request': request}, many=True).data
                response_dict["status"] = True
            else:
                response_dict["error"] = "No purchase details found for this user."
                
        else:
            response_dict["error"] = "Access denied, Only Admin can access the list"

        return Response(response_dict, status=status.HTTP_200_OK)
    

class PurchaseDetailsView(APIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (CustomTokenAuthentication,)

    def get(self, request, pk):
        
        response_dict = {'status': False}
        admin_user = request.user

        if admin_user.user_type == 'ADMIN':
            payment_details = PaymentAttempt.objects.get(parchase__id=pk, user=admin_user, status='succeeded')


            if payment_details.parchase_user_type == 'Subscription':
                all_payment_details = SubscriptionPaymentAttemptsSerializer(payment_details, context = {'request':request}).data
                response_dict["invoice-details"] = all_payment_details
                response_dict["billing-details"] = {
                    'company_name':payment_details.parchase.bill.company_name,
                    'address':payment_details.parchase.bill.address,
                    'billing_contact':payment_details.parchase.bill.billing_contact,
                    'issuing_country':payment_details.parchase.bill.issuing_country,
                    'legal_company_name':payment_details.parchase.bill.legal_company_name,
                    'tax_id':payment_details.parchase.bill.tax_id
                }
                return Response(response_dict, status=status.HTTP_200_OK)
            
            elif payment_details.parchase_user_type == 'User':
                all_payment_details = UserPaymentAttemptsSerializer(payment_details, context = {'request':request}).data
                response_dict["invoice-details"] = all_payment_details
                response_dict["billing-details"] = {
                    'company_name':payment_details.parchase.bill.company_name,
                    'address':payment_details.parchase.bill.address,
                    'billing_contact':payment_details.parchase.bill.billing_contact,
                    'issuing_country':payment_details.parchase.bill.issuing_country,
                    'legal_company_name':payment_details.parchase.bill.legal_company_name,
                    'tax_id':payment_details.parchase.bill.tax_id
                }
                return Response(response_dict, status=status.HTTP_200_OK)
            
            else:
                response_dict["error"]  = "Admin not accosiated with the payment"
                return Response(response_dict, status=status.HTTP_400_BAD_REQUEST)

        else:
            response_dict["error"] = "Acess denied, Only Admin can access the list"
            return Response(response_dict, status=status.HTTP_403_FORBIDDEN)


class CreateCustomRequest(APIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (CustomTokenAuthentication, )

    def post(self, request):
        response_dict = {"status": False}
        bundle_ids = request.data.get("bundle_ids")
        modules_ids = request.data.get("modules_ids")
        name = request.data.get("name")
        email = request.data.get("email")
        phone = request.data.get("phone")

        custom = CustomRequest.objects.create(
            user=request.user,
            status="Pending",
            name=name,
            phone=phone,
            email=email,
        )
        if modules_ids:
            custom.module.add(*request.data.get("modules_ids"))    
        if bundle_ids:  
            custom.bundle.add(*request.data.get("bundle_ids"))    
        response_dict["message"] = "Successfully submitted"
        response_dict["status"] = True
        return Response(response_dict, status=status.HTTP_200_OK)

class ListAdminSubscriptions(APIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (CustomTokenAuthentication, )

    def get(self, request):
        response_dict = {"status": False}
        subscription = SubscriptionDetails.objects.filter(
            user=request.user
        ).last()
        user_subscription = UserSubscriptionDetails.objects.filter(
            user=request.user
        ).last()
        response_dict["subscription"] = SubscriptionParchaseSerializers(subscription).data
        response_dict["user_subscription"] = UserSubscriptionSerializers(user_subscription).data
        response_dict["status"] = True
        return Response(response_dict, status=status.HTTP_200_OK)


class ModulePurchasePriceV2(APIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (CustomTokenAuthentication,)

    def get(self, request):
        subscription_type = request.GET.get("subscription_type")
        bundle_ids = request.GET.getlist("bundle_ids", [])
        modules_ids = request.GET.getlist("modules_ids", [])
        action_type = request.GET.get("action_type")
        
        modules_ids = [ int(x) for x in modules_ids ]
        bundle_ids = [ int(x) for x in bundle_ids ]

        response_dict = {"status":True}
        admin_user = request.user
        current_date = datetime.now().date()
        admin_subscription = SubscriptionDetails.objects.filter(user=admin_user, is_active=True).last()
        
        if action_type == "renew":            
            subscription_type = admin_subscription.subscription_type
            if subscription_type == "WEEK":
                if admin_subscription.subscription_end_date < current_date:
                    subscription_end_date = current_date
                else:
                    subscription_end_date = admin_subscription.subscription_end_date
                new_end_date = subscription_end_date + timedelta(days=7)
                subscription_end_date = new_end_date
            elif subscription_type == "MONTH":
                if admin_subscription.subscription_end_date < current_date:
                    subscription_end_date = current_date
                else:
                    subscription_end_date = admin_subscription.subscription_end_date
                new_end_date = subscription_end_date + timedelta(days=30)
                subscription_end_date = new_end_date
            elif subscription_type == "YEAR":
                if admin_subscription.subscription_end_date < current_date:
                    subscription_end_date = current_date
                else:
                    subscription_end_date = admin_subscription.subscription_end_date
                new_end_date = subscription_end_date + timedelta(days=365)
                subscription_end_date = new_end_date
            
            bundle_price = 0
            module_price = 0
            bundle_module = []
            for i in bundle_ids:
                bundle_obj = BundleDetails.objects.get(id=i)
                bundle_modules = list(bundle_obj.modules.all().values_list("id", flat=True))
                bundle_module.extend(bundle_modules)
                if subscription_type == "WEEK":
                    bundle_price = float(bundle_price) + float(bundle_obj.weekly_price)
                    
                elif subscription_type == "MONTH":
                    bundle_price = float(bundle_price) + float(bundle_obj.monthly_price)
                    
                elif subscription_type == "YEAR":
                    bundle_price = float(bundle_price) + float(bundle_obj.yearly_price)
                    

            for i in modules_ids:
                if i not in bundle_module:
                    module_obj = ModuleDetails.objects.get(id=i)
                    if module_obj.is_submodule == False:
                        if subscription_type == "WEEK":
                            module_price = float(module_price) + float(module_obj.weekly_price)
                            

                        elif subscription_type == "MONTH":
                            module_price = float(module_price) + float(module_obj.monthly_price)
                            
                        elif subscription_type == "YEAR":
                            module_price = float(module_price) + float(module_obj.yearly_price)
                        
            amount = module_price + bundle_price

        elif action_type == "module_bundle_upgrade":
            subscription_end_date = admin_subscription.subscription_end_date
            pending = (subscription_end_date - current_date).days
            bundle_price = 0
            module_price = 0
            bundle_module = []
            already_added_module = admin_subscription.module.all().values_list("id", flat=True)
            already_added_bundle = admin_subscription.bundle.all().values_list("id", flat=True)
            if admin_subscription.subscription_type == "WEEK":
                for i in bundle_ids:
                    bundle_obj = BundleDetails.objects.get(id=i)
                    bundle_modules = list(bundle_obj.modules.all().values_list("id", flat=True))
                    if i not in already_added_bundle:
                        bundle_module.extend(bundle_modules)
                        amount = (bundle_obj.weekly_price / 7) * pending
                        bundle_price = bundle_price + amount
                for i in modules_ids:
                    if i not in bundle_module and i not in already_added_module:
                        module_obj = ModuleDetails.objects.get(id=i)
                        if module_obj.is_submodule == False:
                            amount = (module_obj.weekly_price / 7) * pending
                            module_price = module_price + amount

            elif subscription_type == "MONTH":
                for i in bundle_ids:
                    bundle_obj = BundleDetails.objects.get(id=i)
                    bundle_modules = list(bundle_obj.modules.all().values_list("id", flat=True))
                    if i not in already_added_bundle:
                        bundle_module.extend(bundle_modules)
                        amount = (bundle_obj.monthly_price / 30) * pending
                        bundle_price = bundle_price + amount
                for i in modules_ids:
                    if i not in bundle_module and i not in already_added_module:
                            module_obj = ModuleDetails.objects.get(id=i)
                            if module_obj.is_submodule == False:
                                amount = (module_obj.monthly_price / 30) * pending
                                module_price = module_price + amount

            elif subscription_type == "YEAR":
                for i in bundle_ids:
                    bundle_obj = BundleDetails.objects.get(id=i)
                    bundle_modules = list(bundle_obj.modules.all().values_list("id", flat=True))
                    if i not in already_added_bundle:
                        bundle_module.extend(bundle_modules)
                        amount = (bundle_obj.yearly_price / 365) * pending
                        bundle_price = bundle_price + amount
                for i in modules_ids:
                    if i not in bundle_module and i not in already_added_module:
                        module_obj = ModuleDetails.objects.get(id=i)
                        if module_obj.is_submodule == False:
                            amount = (module_obj.yearly_price / 365) * pending
                            module_price = module_price + amount

            amount = bundle_price + module_price

        elif action_type == "plan_upgrade":
            bundle_price = 0
            module_price = 0
            bundle_module = []
            already_added_module = admin_subscription.module.all().values_list("id", flat=True)
            already_added_bundle = admin_subscription.bundle.all().values_list("id", flat=True)
            
            if admin_subscription.subscription_type == "WEEK":
                if subscription_type == "MONTH":
                    subscription_end_date = admin_subscription.subscription_end_date
                    new_end_date = current_date + timedelta(days=30)
                    pending = (new_end_date - subscription_end_date).days
                    bundle_module = []
                    for i in bundle_ids:
                        bundle_obj = BundleDetails.objects.get(id=i)
                        bundle_modules = list(bundle_obj.modules.all().values_list("id", flat=True))
                        bundle_module.extend(bundle_modules)
                        pending_amount = (bundle_obj.monthly_price / 30) * pending
                        bundle_price = bundle_price + pending_amount
                    for i in modules_ids:
                        module_obj = ModuleDetails.objects.get(id=i)
                        if module_obj.is_submodule == False:
                            if i not in bundle_module:
                                pending_amount = (module_obj.monthly_price / 30) * pending
                                module_price = module_price + pending_amount
                elif subscription_type == "YEAR":
                    subscription_end_date = admin_subscription.subscription_end_date
                    new_end_date = current_date + timedelta(days=365)
                    pending = (new_end_date - subscription_end_date).days
                    bundle_module = []
                    for i in bundle_ids:
                        bundle_obj = BundleDetails.objects.get(id=i)
                        bundle_modules = list(bundle_obj.modules.all().values_list("id", flat=True))
                        bundle_module.extend(bundle_modules)
                        pending_amount = (bundle_obj.yearly_price / 365) * pending
                        bundle_price = bundle_price + pending_amount
                    for i in modules_ids:
                        module_obj = ModuleDetails.objects.get(id=i)
                        if i not in bundle_module:
                            if module_obj.is_submodule == False:
                                pending_amount = (module_obj.yearly_price / 365) * pending
                                module_price = module_price + pending_amount
                amount = module_price + bundle_price
                subscription_end_date = new_end_date
            elif admin_subscription.subscription_type == "MONTH":
                if subscription_type == "YEAR":
                    subscription_end_date = admin_subscription.subscription_end_date
                    new_end_date = current_date + timedelta(days=365)
                    pending = (new_end_date - subscription_end_date).days
                    bundle_module = []
                    for i in bundle_ids:
                        bundle_obj = BundleDetails.objects.get(id=i)
                        bundle_modules = list(bundle_obj.modules.all().values_list("id", flat=True))
                        bundle_module.extend(bundle_modules)
                        pending_amount = (bundle_obj.yearly_price / 365) * pending
                        bundle_price = bundle_price + pending_amount
                    for i in modules_ids:
                        module_obj = ModuleDetails.objects.get(id=i)
                        if i not in bundle_module:
                            if module_obj.is_submodule == False:
                                pending_amount = (module_obj.yearly_price / 365) * pending
                                module_price = module_price + pending_amount

                amount = module_price + bundle_price
                subscription_end_date = new_end_date

        elif action_type == "both_upgrade":
            current_date = datetime.now().date()
            bundle_price = 0
            module_price = 0
            bundle_module = []
            already_added_module = admin_subscription.module.all().values_list("id", flat=True)
            already_added_bundle = admin_subscription.bundle.all().values_list("id", flat=True)
            if admin_subscription.subscription_type == "WEEK":
                if subscription_type == "MONTH":
                    subscription_end_date = admin_subscription.subscription_end_date
                    new_end_date = current_date + timedelta(days=30)
                    pending = (new_end_date - subscription_end_date).days
                    for i in bundle_ids:
                        bundle_obj = BundleDetails.objects.get(id=i)
                        bundle_modules = list(bundle_obj.modules.all().values_list("id", flat=True))
                        bundle_module.extend(bundle_modules)
                        if i not in already_added_bundle:
                            amount = bundle_obj.monthly_price
                            bundle_price = bundle_price + amount
                        else:
                            pending_amount = (bundle_obj.monthly_price / 30) * pending
                            bundle_price = bundle_price + pending_amount
                    for i in modules_ids:
                        module_obj = ModuleDetails.objects.get(id=i)
                        if module_obj.is_submodule == False:
                            if i not in bundle_module and i not in already_added_module:
                                amount = module_obj.monthly_price
                                module_price = module_price + amount
                            elif i in already_added_module:
                                pending_amount = (module_obj.monthly_price / 30) * pending
                                module_price = module_price + pending_amount

                elif subscription_type == "YEAR":
                    subscription_end_date = admin_subscription.subscription_end_date
                    new_end_date = current_date + timedelta(days=365)
                    pending = (new_end_date - subscription_end_date).days
                    for i in bundle_ids:
                        bundle_obj = BundleDetails.objects.get(id=i)
                        bundle_modules = list(bundle_obj.modules.all().values_list("id", flat=True))
                        bundle_module.extend(bundle_modules)
                        if i not in already_added_bundle:
                            amount = bundle_obj.yearly_price
                            bundle_price = bundle_price + amount
                        else:
                            pending_amount = (bundle_obj.yearly_price / 365) * pending
                            bundle_price = bundle_price + pending_amount
                    for i in modules_ids:
                        module_obj = ModuleDetails.objects.get(id=i)
                        if module_obj.is_submodule == False:
                            if i not in bundle_module and i not in already_added_module:
                                amount = module_obj.yearly_price
                                module_price = module_price + amount
                            elif i in already_added_module:
                                pending_amount = (module_obj.yearly_price / 365) * pending
                                module_price = module_price + pending_amount

                amount = module_price + bundle_price
                subscription_end_date = new_end_date
            
            elif admin_subscription.subscription_type == "MONTH":
                if subscription_type == "YEAR":
                    subscription_end_date = admin_subscription.subscription_end_date
                    new_end_date = current_date + timedelta(days=365)
                    pending = (new_end_date - subscription_end_date).days
                    for i in bundle_ids:
                        bundle_obj = BundleDetails.objects.get(id=i)
                        bundle_modules = list(bundle_obj.modules.all().values_list("id", flat=True))
                        bundle_module.extend(bundle_modules)
                        if i not in already_added_bundle:
                            amount = bundle_obj.yearly_price
                            bundle_price = bundle_price + amount
                        else:
                            pending_amount = (bundle_obj.yearly_price / 365) * pending
                            bundle_price = bundle_price + pending_amount
                    for i in modules_ids:
                        module_obj = ModuleDetails.objects.get(id=i)
                        if module_obj.is_submodule == False:
                            if i not in bundle_module and i not in already_added_module:
                                amount = module_obj.yearly_price
                                module_price = module_price + amount
                            elif i in already_added_module:
                                pending_amount = (module_obj.yearly_price / 365) * pending
                                module_price = module_price + pending_amount

                amount = module_price + bundle_price
                subscription_end_date = new_end_date
        else:
            bundle_price = 0
            module_price = 0
            bundle_module = []
            for i in bundle_ids:
                bundle_obj = BundleDetails.objects.get(id=i)
                bundle_modules = list(bundle_obj.modules.all().values_list("id", flat=True))
                bundle_module.extend(bundle_modules)
                if subscription_type == "WEEK":
                    bundle_price = float(bundle_price) + float(bundle_obj.weekly_price)
                    subscription_end_date = current_date + timedelta(days=7)
                elif subscription_type == "MONTH":
                    bundle_price = float(bundle_price) + float(bundle_obj.monthly_price)
                    subscription_end_date = current_date + timedelta(days=30)
                elif subscription_type == "YEAR":
                    bundle_price = float(bundle_price) + float(bundle_obj.yearly_price)
                    subscription_end_date = current_date + timedelta(days=365)
            for i in modules_ids:
                if i not in bundle_module:
                    module_obj = ModuleDetails.objects.get(id=i)
                    if module_obj.is_submodule == False:
                        if subscription_type == "WEEK":
                            module_price = float(module_price) + float(module_obj.weekly_price)
                            subscription_end_date = current_date + timedelta(days=7)

                        elif subscription_type == "MONTH":
                            module_price = float(module_price) + float(module_obj.monthly_price)
                            subscription_end_date = current_date + timedelta(days=30)
                        elif subscription_type == "YEAR":
                            module_price = float(module_price) + float(module_obj.yearly_price)
                            subscription_end_date = current_date + timedelta(days=365)
            amount = module_price + bundle_price

        price_data = {
            "added_by": {"id": admin_user.id}, 
            "amount": amount, 
        }

        response_dict["price_data"] = price_data
        response_dict["subscription_end_date"] = subscription_end_date
        return Response(response_dict, status=status.HTTP_200_OK)