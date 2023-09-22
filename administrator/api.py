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

from administrator.models import SubscriptionDetails
from administrator.serializers import (
    DeletedUserLogSerializers,
    ModuleDetailsSerializer, 
    BundleDetailsSerializer,
    BundleDetailsLiteSerializer,
    UserAssignedModuleSerializers
)
from superadmin.models import DeleteUsersLog, ModuleDetails, BundleDetails, UserAssignedModules


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
        print(
            user , "ppp"
        )
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
                {"message": "Module not found."},
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
        print(user_to_delete)
        print(module_to_delete)
        
        if not user_to_delete.module.filter(id=module_id).exists():
            print('message')
            response_dict["message"] = "User is not associated with the specified module"
            return Response(response_dict, status=status.HTTP_400_BAD_REQUEST)
        print("message_out")
        
        user_to_delete.module.remove(module_to_delete)
        
        # import pdb; pdb.set_trace()
        DeleteUsersLog.objects.create(
            deleted_by=request.user,
            user=user_to_delete.user,
            module=module_to_delete,
            user_id = pk
        )

        

        response_dict["message"] = "Successfully deleted the user from the module"
        response_dict["status"] = True

        return Response(response_dict, status=status.HTTP_200_OK)
