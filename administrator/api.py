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
    OuterRef
)
from fiveapp.utils import PageSerializer, localtime

from administrator.models import PurchaseDetails, SubscriptionDetails,  CsvLogDetails, UploadedCsvFiles, AddToCart, CustomRequest, DepartmentWeightage
from administrator.serializers import (
    DeletedUserLogSerializers,
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
    UserPurchaseHistorySerializer
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
                response_dict["total_users"] = user.total_users
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
        modules = ModuleDetails.objects.filter(is_active=True)
        bundles = BundleDetails.objects.filter(is_active=True)
        subscription = SubscriptionDetails.objects.filter(
            user=request.user, is_subscribed=True,
            subscription_end_date__gte=current_date
        ).last()
        if subscription:
            bundles = bundles.exclude(id__in=subscription.bundle.all().values_list("id", flat=True))
            modules = modules.exclude(
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
        modules = ModuleDetails.objects.filter(is_active=True).order_by("module_identifier")
        subscription = SubscriptionDetails.objects.filter(
            user=request.user, 
            is_subscribed=True,
            subscription_end_date__gte=current_date
        ).last()
        subscribed_modules = []
        if subscription:
            subscribed_modules = modules.filter(
                id__in=subscription.module.all().values_list("id", flat=True)
            )
            modules = modules.exclude(id__in=subscription.module.all().values_list("id", flat=True))
            
        response_dict["unsubscribed_modules"] = ModuleDetailsSerializer(modules,context={"request": request}, many=True,).data
        response_dict["subscribed_modules"] = ModuleDetailsSerializer(
            subscribed_modules,context={"request": request, "from_module":True, "admin":request.user}, many=True,).data
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
        if user.user_type == "ADMIN":
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
        if not csv_file:
            response_dict["error"] = "File Not Found"
            return Response(response_dict, status=status.HTTP_400_BAD_REQUEST)
        if module.module_identifier == 1 or  module.module_identifier == 2:
            if not working_type:
                response_dict["error"] = "Type Required"
                return Response(response_dict, status=status.HTTP_400_BAD_REQUEST)
        to_save = []
        decoded_file = csv_file.read().decode('utf-8').splitlines()
        reader = csv.DictReader(decoded_file)

        upload_log = UploadedCsvFiles.objects.create(
            uploaded_by=request.user,
            modules=module,
            csv_file=csv_file,
            working_type=working_type
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
            # Assuming that 'csv_file.modules.csv_file' contains the file
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

        if csv_file.is_report_generated:
            response_dict["error"] = "Report Already generated"
            return Response(response_dict, status=status.HTTP_200_OK)
        
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
            print(log , "pppppppppppp")
            
            response_dict["report"] = log
        
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
        
        if csv_file.modules.module_identifier == 5:
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
                response_dict["user"] = {
                    "id": logined_user.id,
                    "first_name": logined_user.first_name,
                    "last_name": logined_user.last_name,
                    "email": logined_user.email,
                
                }
                response_dict["status"] = True
                response_dict["modules"] = ModuleDetailsSerializer(all_modules, context={'request':request}, many=True).data
                response_dict["additional_users"] = self.get_users_with_password()
                response_dict["invited_users"] = self.get_users_without_password()
                return Response(response_dict, status=status.HTTP_200_OK)
            elif free_subscribed_modules:
                free_subscribed_modules_ids = []
                for i in free_subscribed_modules:
                    if i.module.all():
                        free_subscribed_modules_ids.extend(
                            list(i.module.all().values_list("id", flat=True))
                        )
                free_modules = ModuleDetails.objects.filter(id__in=free_subscribed_modules_ids).order_by("module_identifier")
                response_dict["modules"] = ModuleDetailsSerializer(free_modules, context={'request':request}, many=True).data
                response_dict["additional_users"] = self.get_users_with_password()
                response_dict["invited_users"] = self.get_users_without_password()
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
            print(deleted_user)
            existing_invite = InviteDetails.objects.filter(email=data.get("email")).exists()

            # if user_exists and not deleted_user:
            #     response_dict["error"] = "User already exists"
            #     return Response(response_dict, status=status.HTTP_200_OK)
            
            if existing_invite:
                response_dict["error"] = "User already invited"
                return Response(response_dict, status=status.HTTP_403_FORBIDDEN)

            available_free_user = admin_login.available_free_users
            print(available_free_user)
            available_paid_user = admin_login.available_paid_users
            print(available_paid_user)
            selected_modules = data.get("selected_modules")
            print(selected_modules)
            selected_bundles = data.get("selected_bundles")
            assigned_module_names = []

            if available_free_user>0:
                print("first")
                if deleted_user:
                    if deleted_user and deleted_user.is_free_user == True:
                        print("freeuser")
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
                            print('post')
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
                        'invited_user_name': data.get('name'),
                        'invitation_link': f'http://{current_domain}/accept-reject/{invite_details.id}/'
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
                    # assign module
                    if selected_modules:
                        print("paid if")
                        for module_id in selected_modules:
                            print("for paid")
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

                    html_message = render_to_string('invitation_link.html', {
                        'invited_user_name': data.get('name'),
                        'invitation_link': f'http://{current_domain}/accept-reject/{invite_details.id}/'
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
            # print(users_to_assign)
            for user_id in users_to_assign:
                try:
                    user_profile = UserProfile.objects.get(id=user_id)

                except UserProfile.DoesNotExist:
                    response_dict["error"] = f"User with the ID {user_id} does not exsts"
                    return Response(response_dict, status=status.HTTP_403_FORBIDDEN)
                # print(user_profile,"USE PROFIEL")
                current_date = timezone.now().date()
                free_subscribed_modules = FreeSubscriptionDetails.objects.filter(
                    user=request.user,
                    free_subscription_end_date__gte=current_date,
                    module__id=pk
                )
                subscribed_module = SubscriptionDetails.objects.filter(subscription_end_date__gte=current_date, user=request.user, module=pk).exists()
                # print(subscribed_module)
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
        response_dict = {"status": False}
        user_obj = UserAssignedModules.objects.filter(user__id=pk, module__isnull=False).last()

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
        # print(serializer.data)
        if request.user.user_type == "ADMIN":
            try:
                assign_user = UserProfile.objects.get(id=pk)
            except UserProfile.DoesNotExist:
                response_dict["error"] = f"User with ID {pk} does not exists"
                return Response(response_dict, status=status.HTTP_404_NOT_FOUND)
            
            serializer.is_valid(raise_exception=True)

            module_to_assign = serializer.validated_data.get('module_ids',[])  

            for module_id in module_to_assign:
                # print(type(module_to_assign))
                # print(module_id)
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
        print(pk)
        response_dict = {"status": False}
        admin_user = request.user
        print(admin_user)
        try:
            deleted_user = UserProfile.objects.get(id=pk, created_admin=admin_user, is_active=True)
        except UserProfile.DoesNotExist:
            return Response({"message": "User not found or access denied", "status": False}, status=status.HTTP_404_NOT_FOUND)
        
        try:
            invited_user = InviteDetails.objects.get(id=pk, user=admin_user, is_verified=True)
            print(invited_user)
        except InviteDetails.DoesNotExist:
            return Response({"message": "User not found or access denied", "status": False}, status=status.HTTP_404_NOT_FOUND) 


        try:
            deleted_user_module = UserAssignedModules.objects.get(user=deleted_user)
        except UserAssignedModules.DoesNotExist:
            deleted_user_module = None

        if invited_user:
            invited_user.is_deleted = True
            invited_user.save()

        
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

        # if invited_user:
        #     invited_user.is_verified = False
            
        
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
    
        # assigned_users = UserAssignedModules.objects.filter(
        #     user_created_admin=request.user,
        #     module__id__in=subscribed_module.module.all().values_list("id", flat=True)
        #         ).values_list("user__id", flat=True)
        # user_c  = UserProfile.objects.filter(id__in=assigned_users).count()

        # print(user_c)

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

        weekly_price = 18
        monthly_price = 69
        yearly_price = 800

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
        print(pk)
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

