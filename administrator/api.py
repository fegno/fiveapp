import random
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
    ModuleSToUserserializer,
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

from user.models import LoginOTP, UserProfile
from django.db import transaction
from fiveapp.utils import get_error
from user.serializers import UserSerializer
from django.core.mail import send_mail, EmailMessage
from django.template.loader import render_to_string
from django.contrib.auth import get_user_model



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

        try:
            user_to_delete = UserAssignedModules.objects.get(user__id=pk, user__created_admin=request.user)
            module_to_delete = ModuleDetails.objects.get(id=module_id)
            
            if not user_to_delete.module.filter(id=module_id).exists():
                response_dict["error"] = "User is not associated with the specified module"
                return Response(response_dict, status=status.HTTP_400_BAD_REQUEST)
            user_to_delete.module.remove(module_to_delete)
            
            if DeleteUsersLog.objects.filter(user=user_to_delete.user, module=module_to_delete).exists():
                response_dict["error"] = "Already In deleted mode"
                return Response(response_dict, status=status.HTTP_400_BAD_REQUEST)

            else:
                deleted_user = DeleteUsersLog.objects.create(
                deleted_by=request.user,
                user=user_to_delete.user,
                module=module_to_delete,
                )
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
        if module.title == "Team Indicator":
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
        elif module.title == "Team Workforce Plan Corporate":
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


class GenerateReport(APIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (CustomTokenAuthentication,)

    def post(self, request, pk):
        response_dict = {"status": False}
        week_working_hour = request.data.get("week_working_hour", 0)
        csv_file = UploadedCsvFiles.objects.filter(
            id=pk
        ).first()
        response_dict["module"] = {
            "id":csv_file.modules.id,
            "name":csv_file.modules.title,
            "department":csv_file.modules.department
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
        
        try:
            if csv_file.working_type == "WEEK":
                for i in log:
                    working_hr = float(i.working_hour)

                    if float(i.working_hour) > float(week_working_hour):
                        extra_hr = float(i.working_hour) - float(week_working_hour)
                        i.extra_hour = extra_hr
                        i.save()
                    elif float(i.working_hour) < float(week_working_hour):
                        per_day = float(week_working_hour) / 5
                        abn = float(i.working_hour) / float(per_day)
                        absent = float(5.0) - float(abn)
                        i.absent_days = absent
                        i.save()
                        
            elif csv_file.working_type == "MONTH":
                week_working_hour =float(week_working_hour) *4
                for i in log:
                    working_hr = float(i.working_hour)
                    if float(i.working_hour) > float(week_working_hour):
                        extra_hr = float(i.working_hour) - float(week_working_hour)
                        i.extra_hour = extra_hr
                        i.save()
                    
                    elif float(i.working_hour) < float(week_working_hour):
                        per_day = float(week_working_hour) / 20
                        abn = float(i.working_hour) / float(per_day)
                        absent = float(20.0) - float(abn)
                        i.absent_days = absent
                        i.save()

            csv_file.is_report_generated = True
            csv_file.save()
            response_dict["status"] = True
            response_dict["message"] = "Generated"
        except Exception as e:
            response_dict["error"] = str(e)
        return Response(response_dict, status=status.HTTP_200_OK)
    


class AdminModules(APIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (CustomTokenAuthentication,)
    def get(self, request):
        response_dict={"status":False}
        logined_user =  request.user

        if logined_user.user_type == 'ADMIN':
            if logined_user.free_subscribed == True:
                free_modules = ModuleDetails.objects.all()
                response_dict["modules"] = ModuleDetailsSerializer(free_modules, context={'request':request}, many=True).data
                response_dict["additional_users"] = self.get_users_with_password()
                response_dict["invited_users"] = self.get_users_without_password()
                return Response(response_dict, status=status.HTTP_200_OK)
            else:
                Subscribed_modules = SubscriptionDetails.objects.filter(user=request.user)
                response_dict["modules"] = SubscriptionModuleSerilzer(Subscribed_modules, context={"request":request,}, many=True).data
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
        user_login =  request.user

        if user_login.user_type == 'ADMIN':
            data = request.data
            serializer = UserInviteSerializer(data=data)
            
            if UserProfile.objects.filter(email=data.get("email")).exists():
                response_dict["error"] = "User already exists"
                return Response(response_dict, status=status.HTTP_200_OK)

            admin_user = request.user 
            
            availble_free_user = admin_user.available_free_users
            available_paid_user = admin_user.available_paid_users


            if availble_free_user>0:

                user = UserProfile.objects.create(
                    user_type="USER",
                    username=data.get("email"),
                    email=data.get("email"),
                    first_name=data.get("first_name"),
                    created_admin=admin_user, 
                )
                user.is_free_user = True
                user.save()

                # Assign the user to selected modules
                selected_modules = data.get("selected_modules")
                assigned_module_names = []
                if selected_modules:
                        
                        existing_assign_user = UserAssignedModules.objects.filter(user=user).first()

                        if existing_assign_user:
                            
                            existing_assign_user.module.clear()
                        else:  
                            existing_assign_user = UserAssignedModules.objects.create(user=user)

                        for module_id in selected_modules:
                            try:
                                module = ModuleDetails.objects.get(id=module_id)
                            except ModuleDetails.DoesNotExist:
                                response_dict["error"] = f"Module with ID {module_id} doesn't exist"
                                return Response(response_dict, status=status.HTTP_400_BAD_REQUEST)

                            existing_assign_user.module.add(module)
                            assigned_module_names.append(module.title)

                admin_user.available_free_users -= 1
                admin_user.save()

                # send otp to mail
                email = request.data.get('email')
                mail_subject = 'OTP for registration'
                otp = random_otp_generator()
                LoginOTP.objects.create(
                    email=request.data.get("email"),
                    otp=otp,
                    user_type="USER"
                )
                
                html_message = render_to_string(
                    'register.html', {"otp":otp}
                )
                email = EmailMessage("OTP for Registration", html_message, to=[email])
                email.content_subtype = "html"
                email.send() 

                response_dict["session_data"] = {
                    "id": user.id,
                    "name": user.first_name,
                    "username": user.username,
                    "email": user.email,
                    "id": user.id,
                    "user_type": user.user_type,
                    "created_admin": user.created_admin.id,
                    "assigned_module_names":assigned_module_names
                }
                response_dict["status"] = True
                response_dict["message"] = "Invite OTP Send to mail"
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

                    
                    selected_modules = data.get("selected_modules")
                    assigned_module_names = []

                    if selected_modules:
                        
                        existing_assign_user = UserAssignedModules.objects.filter(user=user).first()

                        if existing_assign_user:
                            
                            existing_assign_user.module.clear() 
                        else:
                            
                            existing_assign_user = UserAssignedModules.objects.create(user=user)

                        for module_id in selected_modules:
                            try:
                                module = ModuleDetails.objects.get(id=module_id)
                            except ModuleDetails.DoesNotExist:
                                response_dict["error"] = f"Module with ID {module_id} doesn't exist"
                                return Response(response_dict, status=status.HTTP_400_BAD_REQUEST)

                            existing_assign_user.module.add(module)
                            assigned_module_names.append(module.title)

                    admin_user.available_paid_users -= 1
                    admin_user.save()

                    # send otp to mail
                    email=request.data.get('email')
                    mail_subject = 'OTP for registration'
                    otp = random_otp_generator()
                    LoginOTP.objects.create(
                        email=request.data.get("email"),
                        otp=otp,
                        user_type="USER"
                    )
                    
                    html_message = render_to_string(
                        'register.html', {"otp":otp}
                    )
                    email = EmailMessage("OTP for Registration", html_message, to=[email])
                    email.content_subtype = "html"
                    email.send() 

                    response_dict["session_data"] = {
                        "id": user.id,
                        "name": user.first_name,
                        "username": user.username,
                        "email": user.email,
                        "id": user.id,
                        "user_type": user.user_type,
                        "created_admin": user.created_admin.id,
                        "assigned_module_names":assigned_module_names
                    }
                    response_dict["status"] = True
                    response_dict["message"] = "Invite OTP Send to mail"
                else:
                    response_dict["message"] = "No paid or free users are available"  
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

        # is_free_subcribed =user.
        if user.free_subscribed == True:
            un_assigned_user = UserProfile.objects.filter(created_admin=user).exclude(userassignedmodules__module=module)  
            # unassigned_user = un_assigned_user.filter(created_admin=user)
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

                subscribed_module = SubscriptionDetails.objects.filter(user=request.user, module=pk).exists()
                # print(subscribed_module)
                if subscribed_module:
                    if UserAssignedModules.objects.filter(user=user_profile).exists():
                        if UserAssignedModules.objects.filter(user=user_profile, module=module).exists():
                            response_dict["message"] = f"User {user_profile.id} is already assigned to module {module.id}"
                        else:
                            user_assign_object = UserAssignedModules.objects.filter(user=user_profile).first()
                            user_assign_object.module.add(module)
                            response_dict["message"] = "User is assigned to the module"
                    else:
                        assign_user = UserAssignedModules.objects.create(user=user_profile)
                        assign_user.module.add(module)
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
        response_dict = {"satatus": False}
        user_obj = UserAssignedModules.objects.filter(user_id=pk).first()

        if user_obj:
            serializer = UserAssignedModuleSerializers(user_obj)
            response_dict["satatus"] = True
            response_dict["modules"] = serializer.data
        else:
            response_dict["message"] = f"User with ID {pk} has no assigned modules"
        return Response(response_dict, status=status.HTTP_200_OK)
    


class DeleteModule(APIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (CustomTokenAuthentication, )

    def post(self, request,user_id, module_id,):
        response_dict = {"status": False}

        try :
            user_to_delete = UserAssignedModules.objects.get(user__id=user_id)
            module_to_delete = ModuleDetails.objects.get(id=module_id)
        except UserAssignedModules.DoesNotExist:
            response_dict["message"] = f"User with the id  does not exists"
            return Response(response_dict, status=status.HTTP_400_BAD_REQUEST)
        except ModuleDetails.DoesNotExist:
            response_dict["message"] = f"Module with the id  does not exists"
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
        try:
            user_obj = UserProfile.objects.get(id=pk, )
        except UserProfile.DoesNotExist:
            response_dict["message"] = f"User with the ID {pk} does not exists"
            return Response(response_dict, status=status.HTTP_400_BAD_REQUEST)
        if user_obj.created_admin.free_subscribed == True:
            unassigned_modules = ModuleDetails.objects.exclude(userassignedmodules__user=user_obj)
            response_dict["unassigned module"] = ModuleDetailsSerializer(unassigned_modules, context={"request":request}, many=True).data
        elif SubscriptionDetails.objects.filter(user=user_obj.created_admin).exists():
            subscribtion = SubscriptionDetails.objects.filter(user=user_obj.created_admin).first()
            subscribed_modules = subscribtion.module.all()
            unassigned_modules = ModuleDetails.objects.exclude(userassignedmodules__user=user_obj)
            available_un_assiged_module = subscribed_modules & unassigned_modules
            response_dict["unassigned module"] = ModuleDetailsSerializer(available_un_assiged_module, context={"request":request}, many=True).data
        else:
            response_dict["message"] = f"Adimin dons not have subscription"
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
                    if UserAssignedModules.objects.filter(user=assign_user, module=module).exists():
                        response_dict["message"] = "User  is already assigned to module"
                    else:
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

        