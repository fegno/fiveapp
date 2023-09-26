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
    SubscriptionModuleSerilzer,
    UserAssignedModuleSerializers,
    CsvSerializers,
    UploadedCsvFilesSerializer,
    UserInviteSerializer
)
from superadmin.models import (
    DeleteUsersLog,
    ModuleDetails, 
    BundleDetails, 
    UserAssignedModules,
  
)
import csv

from user.models import UserProfile
from django.db import transaction
from fiveapp.utils import get_error
from user.serializers import UserSerializer

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



class ListBundleModules(APIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (CustomTokenAuthentication, IsAdmin)

    def get(self, request, pk):
        response_dict = {"status": False}
        response_dict["modules"] = []
        current_date = timezone.now().date()
        modules = ModuleDetails.objects.filter(is_active=True)
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
                    subscribed_modules,context={"request": request, "from_module":True}, many=True,).data
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
                    subscribed_modules,context={"request": request, "from_module":True}, many=True,).data
        
        
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
        ).last()
        subscribed_modules = []
        if subscription:
            subscribed_modules = modules.filter(
                id__in=subscription.module.all().values_list("id", flat=True)
            )
            modules = modules.exclude(id__in=subscription.module.all().values_list("id", flat=True))
            
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
        response_dict = {"status": False}

        csv_file = UploadedCsvFiles.objects.filter(
            id=pk
        ).first()
        response_dict["module"] = {
            "id":csv_file.modules.id,
            "name":csv_file.modules.title,
            "department":csv_file.modules.department
        }
        csvlog = CsvLogDetails.objects.filter(
            uploaded_file__id=pk
        ).filter(
            Q(uploaded_file__uploaded_by=request.user)|
            Q(uploaded_file__uploaded_by__created_admin=request.user)
        ).order_by("id")
        if not csvlog:
            response_dict["error"] = "Log Not Found"
            return Response(response_dict, status=status.HTTP_400_BAD_REQUEST)
        items_per_page = 100
        paginator = Paginator(csvlog, items_per_page)
        page = request.GET.get("page")
        try:
            items = paginator.page(page)
        except PageNotAnInteger:
            items = paginator.page(1)
        except EmptyPage:
            items = paginator.page(paginator.num_pages)
        serialized = CsvSerializers(items, many=True, context={"request":self.request}).data
        items.object_list = serialized
        response_dict["page"] = PageSerializer(items, serialize=False).data
        response_dict["status"] = True
        return Response(response_dict, status=status.HTTP_200_OK)

class UserInviteModule(APIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (CustomTokenAuthentication,)

    def post(self, request):
        response_dict = {"status": False}
        data = request.data

        serializer = UserInviteSerializer(data=data)
        
        if UserProfile.objects.filter(email=data.get("email")).exists():
            response_dict["error"] = "User already exists"
            return Response(response_dict, status=status.HTTP_200_OK)

        admin_user = request.user 
        # available user count
        availble_free_user = admin_user.available_free_users
        available_paid_user = admin_user.available_paid_users


        if availble_free_user>0:

            # Create a new UserProfile instance for the invited user
            user = UserProfile.objects.create(
                user_type="USER",
                username=data.get("email"),
                email=data.get("email"),
                first_name=data.get("first_name"),
                created_admin=admin_user, 
            )
            user.save()

            # Assign the user to selected modules
            selected_modules = data.get("selected_modules")
            assigned_module_names = []
            if selected_modules:
                for module_id in selected_modules:
                    try:
                        module = ModuleDetails.objects.get(id=module_id)
                    except ModuleDetails.DoesNotExist:
                        response_dict["error"] =  f"module with ID {module_id} doesn't exists"
                        return Response(response_dict, status=status.HTTP_400_BAD_REQUEST)
                    
                    if UserAssignedModules.objects.filter(user=user, module=module).exists():
                        response_dict["error"] = f"User with the module ID {module_id} already exists"
                    
                    assign_user = UserAssignedModules.objects.create(user=user)
                    assign_user.module.add(module)
                    assigned_module_names.append(module.title)

            admin_user.available_free_users -= 1
            admin_user.save()

            response_dict["session_data"] = {
                "name": user.first_name,
                "username": user.username,
                "email": user.email,
                "id": user.id,
                "user_type": user.user_type,
                "created_admin": user.created_admin.id,
                "assigned_module_names":assigned_module_names
            }
            response_dict["status"] = True
            response_dict["message"] = "User invitation and module assignment successful"
        else:
            if available_paid_user>0:
                # Create a new UserProfile instance for the invited user
                user = UserProfile.objects.create(
                    user_type="USER",
                    username=data.get("email"),
                    email=data.get("email"),
                    first_name=data.get("first_name"),
                    created_admin=admin_user, 
                )
                user.save()

                # Assign the user to selected modules
                selected_modules = data.get("selected_modules")
                print(selected_modules)
                assigned_module_names = []
                if selected_modules:
                    for module_id in selected_modules:
                        try:
                            module = ModuleDetails.objects.get(id=module_id)
                        except ModuleDetails.DoesNotExist:
                            response_dict["error"] =  f"module with ID {module_id} doesn't exists"
                            return Response(response_dict, status=status.HTTP_400_BAD_REQUEST)
                        
                        if UserAssignedModules.objects.filter(user=user, module=module).exists():
                            response_dict["error"] = f"User with the module ID {module_id} already exists"
                        
                        assign_user = UserAssignedModules.objects.create(user=user)
                        assign_user.module.add(module)
                        assigned_module_names.append(module.title)

                admin_user.available_paid_users -= 1
                admin_user.save()

                response_dict["session_data"] = {
                    "name": user.first_name,
                    "username": user.username,
                    "email": user.email,
                    "id": user.id,
                    "user_type": user.user_type,
                    "created_admin": user.created_admin.id,
                    "assigned_module_names":assigned_module_names
                }
                response_dict["status"] = True
                response_dict["message"] = "User invitation and module assignment successful"
            else:
                response_dict["message"] = "No paid or free users are available"    
        return Response(response_dict, status=status.HTTP_200_OK)


class UnAssignUserlist(APIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (CustomTokenAuthentication,) 

    def get(self, request,pk):
        response_dict = {"status":True}
        user = request.user
        module = ModuleDetails.objects.get(id=pk)
        un_assigned_user = UserProfile.objects.filter(created_admin=user).exclude(userassignedmodules__module=module)  
        # unassigned_user = un_assigned_user.filter(created_admin=user)
        response_dict["un_assigned_users"] = UserSerializer(un_assigned_user, context={"request":request}, many=True).data
        return Response(response_dict, status=status.HTTP_200_OK)


class AssignUser(APIView):
    permission_classes =(IsAuthenticated,)
    authentication_classes = (CustomTokenAuthentication,) 

    def post(self, request, pk):
        response_dict = {"status":True}
        user = request.user
        try:
            module = ModuleDetails.objects.get(id=pk)
        except ModuleDetails.DoesNotExist:
            response_dict["error"] = f"Module with ID {pk} does not exists"
            return Response(response_dict, status=status.HTTP_200_OK)
        

        users_to_assign = request.data.get("user_ids", [])
        for user_id in users_to_assign:
            try:
                users = UserProfile.objects.get(id=user_id)
            except UserProfile.DoesNotExist:
                response_dict["error"] = f"User with the ID {user_id} does not exsts"

            if UserAssignedModules.objects.filter(user=user, module=module).exists():
                continue  

            assign_user = UserAssignedModules.objects.create(user=user)
            assign_user.module.add(module)
        return Response(response_dict, status=status.HTTP_200_OK)
    

    # def post(self, request, module_id):
    #     try:
    #         module = ModuleDetails.objects.get(id=module_id)
    #     except ModuleDetails.DoesNotExist:
    #         return Response({"error": f"Module with ID {module_id} does not exist."}, status=status.HTTP_404_NOT_FOUND)

    #     # Get the list of user IDs to assign to the module from the request data
    #     user_ids_to_assign = request.data.get("user_ids", [])
        
    #     # Loop through user IDs and assign users to the module
    #     for user_id in user_ids_to_assign:
    #         try:
    #             user = UserProfile.objects.get(id=user_id)
    #         except UserProfile.DoesNotExist:
    #             return Response({"error": f"User with ID {user_id} does not exist."}, status=status.HTTP_404_NOT_FOUND)

    #         # Check if the user is already assigned to the module
    #         if UserAssignedModules.objects.filter(user=user, module=module).exists():
    #             continue  # Skip already assigned users

    #         # Create a UserAssignedModules instance to assign the user to the module
    #         assign_user = UserAssignedModules.objects.create(user=user)
    #         assign_user.module.add(module)

    #     return Response({"message": "Users assigned to the module successfully."}, status=status.HTTP_200_OK)




        