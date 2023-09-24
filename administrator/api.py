from django.shortcuts import render
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
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
)
from fiveapp.utils import PageSerializer

from administrator.models import SubscriptionDetails,  CsvLogDetails, UploadedCsvFiles
from administrator.serializers import (
    DeletedUserLogSerializers,
    ModuleDetailsSerializer, 
    BundleDetailsSerializer,
    BundleDetailsLiteSerializer,
    UserAssignedModuleSerializers,
    CsvSerializers,
    UploadedCsvFilesSerializer
)
from superadmin.models import (
    DeleteUsersLog,
    ModuleDetails, 
    BundleDetails, 
    UserAssignedModules,
  
)
import csv

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
            expired_subscription = None
            subscription = SubscriptionDetails.objects.filter(
                user=request.user, is_subscribed=True,
                subscription_end_date__gte=current_date
            ).order_by("-id").first()
            if not subscription:
                expired_subscription = SubscriptionDetails.objects.filter(
                    user=request.user
                ).order_by("-id").first()

            if subscription:
                modules = ModuleDetails.objects.filter(is_active=True).filter(
                    id__in=subscription.module.all().values_list("id", flat=True)
                )
                bundles = BundleDetails.objects.filter(is_active=True, id__in=subscription.bundle.all().values_list("id", flat=True))
                response_dict["bundles"] = BundleDetailsSerializer(bundles,context={"request": request}, many=True).data
                response_dict["modules"] = ModuleDetailsSerializer(modules,context={"request": request}, many=True,).data
                response_dict["status"] = True
                response_dict["take_subscription"] = True
                return Response(response_dict, status=status.HTTP_200_OK)
            elif expired_subscription:
                response_dict["message"] = "Subscription Expired"
                response_dict["status"] = True
                response_dict["take_subscription"] = True
                return Response(response_dict, status=status.HTTP_200_OK)
            elif user.take_free_subscription:
                response_dict["free_subscription"] = True
                if user.free_subscription_end_date and user.free_subscription_end_date > current_date:
                    modules = ModuleDetails.objects.filter(is_active=True)
                    bundles = BundleDetails.objects.filter(is_active=True)
                    response_dict["bundles"] = BundleDetailsSerializer(bundles,context={"request": request}, many=True).data
                    response_dict["modules"] = ModuleDetailsSerializer(modules,context={"request": request}, many=True,).data
                else:
                    response_dict["message"] = "Free Subscription Expired"
                response_dict["take_subscription"] = True
                response_dict["status"] = True
                return Response(response_dict, status=status.HTTP_200_OK)
            else:
                response_dict["error"] = "Not started your any subscription"
                return Response(response_dict, status=status.HTTP_403_FORBIDDEN)
        elif user.user_type == "USER":
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
                    id__in=subscription.module.all().values_list("id", flat=True)
                )
                response_dict["modules"] = ModuleDetailsSerializer(modules,context={"request": request}, many=True,).data
                response_dict["status"] = True
                response_dict["take_subscription"] = True
                return Response(response_dict, status=status.HTTP_200_OK)
            elif expired_subscription:
                response_dict["message"] = "Subscription Expired"
                response_dict["status"] = True
                response_dict["take_subscription"] = True
                return Response(response_dict, status=status.HTTP_200_OK)
            elif admin.take_free_subscription:
                response_dict["free_subscription"] = True
                if admin.free_subscription_end_date and admin.free_subscription_end_date > current_date:
                    modules = ModuleDetails.objects.filter(is_active=True, id__in=modules_list)
                    response_dict["modules"] = ModuleDetailsSerializer(modules,context={"request": request}, many=True,).data
                else:
                    response_dict["message"] = "Free Subscription Expired"
                response_dict["take_subscription"] = True
                response_dict["status"] = True
                return Response(response_dict, status=status.HTTP_200_OK)
            else:
                response_dict["error"] = "Not started your any subscription"
                return Response(response_dict, status=status.HTTP_403_FORBIDDEN)

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
        )
        if subscription:
            bundles = bundles.exclude(id__in=subscription.bundle.all().values_list("id", flat=True))
            modules = modules.exclude(
                id__in=subscription.modules.all().values_list("id", flat=True)
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

class ListModules(APIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (CustomTokenAuthentication, IsAdmin)

    def get(self, request):
        response_dict = {"status": False}
        current_date = timezone.now().date()
        modules = ModuleDetails.objects.filter(is_active=True)
        subscription = SubscriptionDetails.objects.filter(
            user=request.user, 
            is_subscribed=True,
            subscription_end_date__gte=current_date
        )
        subscribed_modules = []
        if subscription:
            subscribed_modules = modules.exclude(
                id__in=subscription.modules.all().values_list("id", flat=True)
            )
            modules = modules.exclude(id__in=subscription.modules.all().values_list("id", flat=True))
            
        response_dict["unsubscribed_modules"] = ModuleDetailsSerializer(modules,context={"request": request}, many=True,).data
        response_dict["subscribed_modules"] = ModuleDetailsSerializer(
            subscribed_modules,context={"request": request, "from_module":True}, many=True,).data
        response_dict["status"] = True
        return Response(response_dict, status=status.HTTP_200_OK)

class SelectFreeSubscription(APIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (CustomTokenAuthentication, IsAdmin)

    def post(self, request):
        response_dict = {"status": False}
        user = request.user
        if user.take_free_subscription:
            response_dict["error"] = "Already subscribed"
            return Response(response_dict, status.HTTP_200_OK)
        user.take_free_subscription = True
        user.free_subscribed = True
        user.free_subscription_start_date = timezone.now().date()
        user.free_subscription_end_date = timezone.now().date()  + timedelta(days=15)
        user.save()
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

        user_to_delete = UserAssignedModules.objects.get(user__id=pk)
        module_to_delete = ModuleDetails.objects.get(id=module_id)
        
        if not user_to_delete.module.filter(id=module_id).exists():
            response_dict["error"] = "User is not associated with the specified module"
            return Response(response_dict, status=status.HTTP_400_BAD_REQUEST)
        user_to_delete.module.remove(module_to_delete)
        
        DeleteUsersLog.objects.create(
            deleted_by=request.user,
            user=user_to_delete.user,
            module=module_to_delete,
            user_id = pk
        )
        response_dict["message"] = "Successfully deleted the user from the module"
        response_dict["status"] = True
        return Response(response_dict, status=status.HTTP_200_OK)


class UploadCsv(APIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (CustomTokenAuthentication,)

    def post(self, request, pk):
        response_dict = {"status": False}
        csv_file = request.FILES.get("file")
        working_type = request.FILES.get("working_type")

        module = ModuleDetails.objects.filter(id=pk).last()
        if not module:
            response_dict["error"] = "Module Not Found"
            return Response(response_dict, status=status.HTTP_400_BAD_REQUEST)
        if not csv_file:
            response_dict["error"] = "Module Not Found"
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
        for row in reader:
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
        CsvLogDetails.objects.bulk_create(to_save)
        response_dict["message"] = "Successfully uplaoded"
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
        csv_log = UploadedCsvFiles.objects.filter(
            modules=module
        ).filter(
            Q(uploaded_by=request.user)|
            Q(uploaded_by__created_admin=request.user)
        )
        items_per_page = 100
        paginator = Paginator(csv_log, items_per_page)
        page = request.GET.get("page")
        try:
            items = paginator.page(page)
        except PageNotAnInteger:
            items = paginator.page(1)
        except EmptyPage:
            items = paginator.page(paginator.num_pages)
        serialized = UploadedCsvFilesSerializer(items, many=True, context={"request":self.request}).data
        items.object_list = serialized
        response_dict["page"] = PageSerializer(items, serialize=False).data
        response_dict["status"] = True
        return Response(response_dict, status=status.HTTP_200_OK)
