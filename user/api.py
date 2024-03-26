import re
import string
import random
from django.forms import ValidationError
from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.contrib.auth import authenticate
from django.templatetags.static import static
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from django.contrib.auth import login, logout

from django.utils import timezone
from superadmin.models import InviteDetails

from user.api_permissions import CustomTokenAuthentication
from django.db.models import BooleanField, Case, Q, Sum, Value, When
from django.db import transaction

from datetime import date, timedelta, datetime
import json
import os
import shlex
import subprocess
from background_task import background
from fiveapp.utils import get_error

from user.models import BillingDetails, CardDetails, UserProfile, Token, LoginOTP, ForgotOTP
from user.serializers import BillingDetailsSerializer, CardDetailsSerializer, RegisterSerializer, UserSerializer
from user.task import send_mail
from rest_framework import status
from django.core.mail import send_mail, EmailMessage
from django.template.loader import render_to_string

from django.utils.encoding import force_text
from django.utils.http import urlsafe_base64_decode


def process_tasks():
    process_tasks_cmd = "python manage.py process_tasks"
    process_tasks_args = shlex.split(process_tasks_cmd)
    process_tasks_subprocess = subprocess.Popen(process_tasks_args)


def random_otp_generator(size=4, chars="123456789"):
    return "".join(random.choice(chars) for _ in range(size))


class Applogin(APIView):
    permission_classes = (AllowAny,)
    authentication_classes = tuple()

    def post(self, request):
        response_dict = {"status": False}
        email = request.data.get("email")
        password = request.data.get("password")
        if email == None or email == "null":
            response_dict["message"] = "Email cannot be empty"
            return Response(response_dict, HTTP_200_OK)
        
        if email:
            user = UserProfile.objects.get(email=email)
            if user.is_active == True:
                authenticated = authenticate(username=email, password=password)
                if authenticated:
                    user = get_object_or_404(UserProfile, username=email)
                    user.save()
                    flag = 1
                else:
                    response_dict["message"] = "Username or password incorrect"
                    return Response(response_dict, status=status.HTTP_400_BAD_REQUEST)
            else:
                response_dict["message"] = "User is deleted"
                return Response(response_dict, status=status.HTTP_400_BAD_REQUEST)
        else:
            response_dict["message"] = "Login Method DoesNotExist"
            return Response(response_dict, HTTP_200_OK)
        
        if user.user_type == "USER" and not user.is_free_user:
            now_date = timezone.now().date()
            if user.subscription_end_date and user.subscription_end_date < now_date:
                response_dict["error"] = "Subscription expired please contact admin"
                return Response(response_dict, status=status.HTTP_400_BAD_REQUEST)
            elif not user.subscription_end_date:
                response_dict["error"] = "Not Subscribed"
                return Response(response_dict, status=status.HTTP_400_BAD_REQUEST)
        if flag == 1 or tok == 1:
            Token.objects.filter(user=user).delete()
            token, c = Token.objects.get_or_create(user=user)
            response_dict["session_data"] = {
                "token": token.key,
                "name": user.first_name,
                "username": user.username,
                "email": user.email,
                "id": user.id,
                'user_type':user.user_type,
                "free_subscribed":True if user.take_free_subscription else False,
                "subscribed":True if user.is_subscribed else False
            }
            response_dict["token"] = token.key
            response_dict["status"] = True
            return Response(response_dict, HTTP_200_OK)
        return Response(response_dict, status=status.HTTP_400_BAD_REQUEST)

class VerifyEmail(APIView):
    permission_classes = (AllowAny,)
    authentication_classes = tuple()

    def post(self, request):
        response_dict = {"status": False}
        email = request.data.get("email")
        created_otp = UserProfile.objects.filter(
            email=email,
        ).order_by("-id").first()
        if not created_otp:
            response_dict["message"] = "Verified"
            response_dict["status"] = True
        else:
            response_dict["error"] = "Email already added by someone"
            response_dict["User_type"] = created_otp.user_type
            created_admin_email = created_otp.created_admin.email if created_otp.created_admin else None
            response_dict["Created_by"] = created_admin_email
            response_dict["status"] = False
        return Response(response_dict, HTTP_200_OK)



class SendOtp(APIView):
    permission_classes = (AllowAny,)
    authentication_classes = tuple()

    def post(self, request):
        response_dict = {"status": False}
        email = request.data.get("email")
        mail_subject = 'OTP for registration'
        otp = random_otp_generator()
        LoginOTP.objects.create(
            email=request.data.get("email"),
            otp=otp,
            user_type="ADMIN"
        )
        
        html_message = render_to_string(
            'register.html', {"otp":otp}
        )
        email = EmailMessage("OTP for Registration", html_message, to=[email])
        email.content_subtype = "html"
        email.send()   

        response_dict["message"] = "OTP send to email"
        response_dict["status"] = True
        return Response(response_dict, HTTP_200_OK)

class VerifyOtp(APIView):
    permission_classes = (AllowAny,)
    authentication_classes = tuple()

    def post(self, request):
        response_dict = {"status": False}
        email = request.data.get("email")
        otp = request.data.get("otp")
        created_otp = LoginOTP.objects.filter(
            email=email,
        ).order_by("-id").first()
        if created_otp and created_otp.is_verified:
            response_dict["error"] = "OTP already Verfied"
            response_dict["status"] = False
            return Response(response_dict, HTTP_200_OK)
        if created_otp and str(created_otp.otp) == str(otp):
            created_otp.is_verified = True
            created_otp.save()
            response_dict["message"] = "Success"
            response_dict["status"] = True
        else:
            response_dict["error"] = "OTP incorrect"
            response_dict["status"] = False
        return Response(response_dict, HTTP_200_OK)


class RegisterUser(APIView):
    permission_classes = (AllowAny,)
    authentication_classes = tuple()

    def post(self, request):
        response_dict = {"status": False}
        data = request.data   
        if not LoginOTP.objects.filter(email=data.get("email"), is_verified=True).last():
            response_dict["error"] = "OTP not verified"
            return Response(response_dict, HTTP_200_OK)
        serializer = RegisterSerializer(data=data)
        if UserProfile.objects.filter(
            email=data.get("email"),
        ).first():
            response_dict["error"] ="User already exists"
            return Response(response_dict, HTTP_200_OK)
        
        if serializer.is_valid():
            errors = []

            if len(data.get("password")) < 5:
                errors.append("Password must have at least 5 characters.")
            if not re.search("[a-zA-Z]", data.get("password")):
                errors.append("Password must contain at least one letter.")
            if not re.search("[0-9]", data.get("password")):
                errors.append("Password must contain at least one number.")

            if errors:
                response_dict["error"] = ", ".join(errors)
                return Response(response_dict, status=status.HTTP_400_BAD_REQUEST)
            
            with transaction.atomic():
                user = serializer.save(
                    user_type="ADMIN",
                )
                user.username = user.email
                user.set_password(data.get("password"))
                user.save()
                authenticated = authenticate(username=user.email, password=data.get("password"))
                Token.objects.filter(user=user).delete()
                token, c = Token.objects.get_or_create(user=user)
                response_dict["session_data"] = {
                    "token": token.key,
                    "name": user.first_name,
                    "username": user.username,
                    "email": user.email,
                    "id": user.id,
                    'user_type':user.user_type,
                    "free_subscribed":True if user.take_free_subscription else False,
                    "subscribed":True if user.is_subscribed else False
                }
                response_dict["token"] = token.key
                response_dict["status"] = True
        else:
            response_dict["error"] = get_error(serializer)
        
        return Response(response_dict, status=status.HTTP_200_OK)
            

class AppLogout(APIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (CustomTokenAuthentication,)

    def post(self, request):
        logout(request)
        response_dict = {"status": True}
        response_dict["message"] = "Logout successfully"
        return Response(response_dict, HTTP_200_OK)


class SetUserPassword(APIView):
    permission_classes = (AllowAny,)
    authentication_classes = tuple()

    def post(self, request):
        response_dict = {"status": False}
        email = request.data.get("email") 
        new_password = request.data.get("new_password") 
        confirm_password  = request.data.get("confirm_password") 

        errors = []

        if len(new_password) < 5:
            errors.append("Password must have at least 5 characters.")
        if not re.search("[a-zA-Z]", new_password):
            errors.append("Password must contain at least one letter.")
        if not re.search("[0-9]", new_password):
            errors.append("Password must contain at least one number.")
        if new_password != confirm_password:
            errors.append("Passwords do not match.")

        if errors:
            response_dict["error"] = ", ".join(errors)
            return Response(response_dict, status=status.HTTP_400_BAD_REQUEST)

        user = UserProfile.objects.filter(username=email).first()
        user.set_password(new_password)
        user.save()
        response_dict["status"] = True
        response_dict["message"] = "Password created"
        return Response(response_dict, HTTP_200_OK)

class ForgotPasswordOtp(APIView):
    permission_classes = (AllowAny,)
    authentication_classes = tuple()

    def post(self, request):
        response_dict = {"status": False}
        email = request.data.get("email") 
        user = UserProfile.objects.filter(
            username=email
        ).last()
        if not user:
            response_dict["error"] = "user does not exists"
            return Response(response_dict, HTTP_200_OK)

        otp = random_otp_generator()
        ForgotOTP.objects.create(
            email=request.data.get("email"),
            otp=otp,
        )
        html_message = render_to_string('forgot-password.html', {"otp": otp})
        email = EmailMessage("OTP for forgot password", html_message, to=[email])
        email.content_subtype = "html"
        email.send()
        response_dict["status"] = True
        response_dict["message"] = "otp sent to the email"
        return Response(response_dict, HTTP_200_OK)

class ForgotVerifyOtp(APIView):
    permission_classes = (AllowAny,)
    authentication_classes = tuple()

    def post(self, request):
        response_dict = {"status": False}
        email = request.data.get("email")
        otp = request.data.get("otp")
        created_otp = ForgotOTP.objects.filter(
            email=email,
        ).order_by("-id").first()
        if created_otp and created_otp.is_verified:
            response_dict["error"] = "OTP already Verfied"
            response_dict["status"] = False
            return Response(response_dict, HTTP_200_OK)
        if created_otp and str(created_otp.otp) == str(otp):
            created_otp.is_verified = True
            created_otp.save()
            response_dict["message"] = "Success"
            response_dict["status"] = True
        else:
            response_dict["error"] = "OTP incorrect"
            response_dict["status"] = False
        return Response(response_dict, HTTP_200_OK)

class ForgotPassword(APIView):
    permission_classes = (AllowAny,)
    authentication_classes = tuple()

    def post(self, request):
        response_dict = {"status": False}
        email = request.data.get("email") 
        new_password = request.data.get("new_password") 
        confirm_password  = request.data.get("confirm_password") 

        created_otp = ForgotOTP.objects.filter(
            email=email,
        ).order_by("-id").first()
        if created_otp and not created_otp.is_verified:
            response_dict["error"] = "Otp not verified"
            return Response(response_dict, HTTP_200_OK)


        user = UserProfile.objects.filter(
            username=email
        ).last()
        if not user:
            response_dict["error"] = "user does not exists"
            return Response(response_dict, HTTP_200_OK)
        
        errors = []

        if len(new_password) < 5:
            errors.append("Password must have at least 5 characters.")
        if not re.search("[a-zA-Z]", new_password):
            errors.append("Password must contain at least one letter.")
        if not re.search("[0-9]", new_password):
            errors.append("Password must contain at least one number.")
        if new_password != confirm_password:
            errors.append("Passwords do not match.")

        if errors:
            response_dict["error"] = ", ".join(errors)
            return Response(response_dict, status=status.HTTP_400_BAD_REQUEST)
        
        user.set_password(new_password)
        user.save()
        response_dict["status"] = True
        response_dict["message"] = "Password changed"
        return Response(response_dict, HTTP_200_OK)

class ChangePassword(APIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (CustomTokenAuthentication,)

    def post(self, request):
        response_dict = {"status": False}
        user = request.user
        old_password = request.data.get("old_password") 
        new_password = request.data.get("new_password") 
        confirm_password  = request.data.get("confirm_password") 

        if not user.check_password(old_password):
            response_dict["error"] = "Old Password is incorrect"
            return Response(response_dict, HTTP_200_OK)

        errors = []

        if len(new_password) < 5:
            errors.append("Password must have at least 5 characters.")
        if not re.search("[a-zA-Z]", new_password):
            errors.append("Password must contain at least one letter.")
        if not re.search("[0-9]", new_password):
            errors.append("Password must contain at least one number.")
        if new_password != confirm_password:
            errors.append("Passwords do not match.")

        if errors:
            response_dict["error"] = ", ".join(errors)
            return Response(response_dict, status=status.HTTP_400_BAD_REQUEST)
        
        user.set_password(new_password)
        user.save()
        response_dict["status"] = True
        response_dict["message"] = "Password changed"
        return Response(response_dict, HTTP_200_OK)
    

class ChangeName(APIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (CustomTokenAuthentication,)

    def post(self, request):
        response_dict ={"status":False}
        user = request.user
        first_name =  request.data.get("first_name")
        last_name = request.data.get("last_name")
        user.first_name = first_name
        user.last_name = last_name
        user.save()
        response_dict["status"] = True
        response_dict["message"] = "successfully Update the name"
        return Response(response_dict, HTTP_200_OK)
    

class ChangeComapnyName(APIView):

    permission_classes = (IsAuthenticated,)
    authentication_classes = (CustomTokenAuthentication,)

    def post(self, request):
        response_dict ={"status":False}
        user = request.user
        company_name = request.data.get('company_name')
        user.company_name = company_name
        user.save()
        response_dict["message"] = "successfully update the Company name"
        response_dict["status"] = True
        return Response(response_dict, HTTP_200_OK)
    

class ChangeEmail(APIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (CustomTokenAuthentication,)

    def post(self, request):
        response_dict ={"status":False}
        email = request.data.get('email')
        user = request.user
        email_exist = UserProfile.objects.filter(username=email).exists()
        if email_exist:
            response_dict["error"] = "The email already in use"
            return Response(response_dict, status=status.HTTP_400_BAD_REQUEST)
        elif user.username == email:
            response_dict["error"] = "The email already used as username"
            return Response(response_dict, status=status.HTTP_400_BAD_REQUEST)
        
        otp = random_otp_generator()
        LoginOTP.objects.create(
            email=request.data.get("email"),
            otp=otp,
            user_type=user.user_type
        )

        html_message = render_to_string('email-change.html', {"otp": otp,"user":user})

        email = EmailMessage("OTP for email change", html_message, to=[email])
        email.content_subtype = "html"
        email.send()

        # old_email = user.email
        # LoginOTP.objects.filter(email=old_email).update(email=email)
        # user.email = email
        # user.username = email
        # user.save()
        
        response_dict["message"] = "OTP send to email"
        response_dict["status"] = True
        return Response(response_dict, HTTP_200_OK)
    


class UpdateEmail(APIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (CustomTokenAuthentication,)

    def post(self, request):
        response_dict ={"status":False}
        email = request.data.get('email')
        user = request.user
        email_exist = UserProfile.objects.filter(username=email).exists()
        if email_exist:
            response_dict["error"] = "The email already in use"
            return Response(response_dict, HTTP_200_OK)
        elif user.username == email:
            response_dict["error"] = "The email already used as username"
            return Response(response_dict, HTTP_200_OK)
        

        old_email = user.email
        LoginOTP.objects.filter(email=old_email, is_verified=True).update(email=email)
        user.email = email
        user.username = email
        user.save()
        
        response_dict["message"] = "Email Updated"
        response_dict["status"] = True
        return Response(response_dict, HTTP_200_OK) 



class UserDetail(APIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (CustomTokenAuthentication,)

    def get(self, request):
        response_dict = {"status": False}
        user_serializer = UserSerializer(request.user)
        response_dict["details"] = user_serializer.data
        response_dict["status"] = True
        return Response(response_dict, status=status.HTTP_200_OK)

class CheckLoginMethod(APIView):
    permission_classes = (AllowAny,)
    authentication_classes = tuple()

    def get(self, request):
        response_dict = {"status": False}
        data = request.GET
        email = request.GET.get("email")
        user = UserProfile.objects.filter(
            email=data.get("email"),
        ).first()
        
        invited_user = InviteDetails.objects.filter(
            email=data.get("email")
        ).last()

        if user and user.user_type == "ADMIN":
            response_dict["user_type"] = "ADMIN"
            response_dict["password_set"] = True
        elif user:
            if user.password:
                response_dict["password_set"] = True
                response_dict["user_type"] = "USER"
                created_admin_email = user.created_admin.email if user.created_admin else None
                response_dict["Created_by"] = created_admin_email
            else:
                response_dict["password_set"] = False
                response_dict["user_type"] = "USER"
                created_admin_email = user.created_admin.email if user.created_admin else None
                response_dict["Created_by"] = created_admin_email
        elif invited_user:
            response_dict["password_set"] = False
            response_dict["user_type"] = "USER"
            created_admin_email = invited_user.user.email if invited_user.user else None
            response_dict["Created_by"] = created_admin_email
            response_dict["message"] = f'You are invited as User, Created/Invited by {created_admin_email}'
        elif not user:
            if LoginOTP.objects.filter(email=email, is_verified=True):
                otp_user = LoginOTP.objects.filter(email=email).order_by('id').last()
                response_dict["password_set"] = False
                response_dict["user_type"] = otp_user.user_type
            else:
                response_dict["user_type"] = "Not Registered"
                response_dict["password_set"] = False

        response_dict["status"] = True
        return Response(response_dict, status=status.HTTP_200_OK)
    

class BillingDetailsCreateView(APIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (CustomTokenAuthentication,)

    def post(self, request):
        response_dict = {'status': False}
        serializer = BillingDetailsSerializer(data=request.data)  

        if request.user.user_type == 'ADMIN':
            if serializer.is_valid():
                billing_details = serializer.save(user=request.user) 
                response_dict = {
                    'id': billing_details.id,
                    'user': billing_details.user.id,
                    'company_name': billing_details.company_name,
                    'address': billing_details.address,
                    'billing_contact': billing_details.billing_contact,
                    'issuing_country': billing_details.issuing_country,
                    'legal_company_name': billing_details.legal_company_name,
                    'tax_id': billing_details.tax_id
                }
                response_dict["status"] = True
                return Response(response_dict, status=status.HTTP_201_CREATED)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            response_dict["error"] = "Access Denied"
            return Response(response_dict,status=status.HTTP_403_FORBIDDEN)
        
    
class BillingDetailsListView(APIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (CustomTokenAuthentication,)

    def get(self, request):
        response_dict = {'status':False}
        billing_list = BillingDetails.objects.filter(user=request.user)
        if request.user.user_type == 'ADMIN':
            if billing_list:
                response_dict["billing_list"] = BillingDetailsSerializer(billing_list, context={'request':request}, many=True).data
                response_dict["status"] = True
                return Response(response_dict, status=status.HTTP_200_OK)
            else:
                response_dict["billing_list"] = BillingDetailsSerializer(billing_list, context={'request':request}, many=True).data
                return Response(response_dict, status=status.HTTP_200_OK)
        else:
            response_dict["error"] = "Access Denied"
            return Response(response_dict,status=status.HTTP_403_FORBIDDEN)
        

class BillingDetailsEdit(APIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (CustomTokenAuthentication,)

    def put(self, request, pk):
        response_dict = {'status':False}
        user = request.user
        
        if user.user_type == 'ADMIN':
            billing_details = BillingDetails.objects.get(id=pk, user=user)
            if not billing_details:
                return Response({'error': 'Billing details not found for this user.'}, status=status.HTTP_404_NOT_FOUND)

            serializer = BillingDetailsSerializer(billing_details, data=request.data, partial=True)

            if serializer.is_valid():
                billing_obj = serializer.save()
                response_dict = {
                        'id': billing_obj.id,
                        'user': billing_obj.user.id,
                        'company_name': billing_obj.company_name,
                        'address': billing_obj.address,
                        'billing_contact': billing_obj.billing_contact,
                        'issuing_country': billing_obj.issuing_country,
                        'legal_company_name': billing_obj.legal_company_name,
                        'tax_id': billing_obj.tax_id
                    }
                return Response(response_dict, status=status.HTTP_200_OK)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            response_dict["error"] = "Access Denied, Only Admin acan access this"
    
        

class BillingDetailsDelete(APIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (CustomTokenAuthentication,)

    def delete(self, request, pk):
        response_dict = {'status':False}
        
        if request.user.user_type == 'ADMIN':
            billing_obj = BillingDetails.objects.get(id=pk, user=request.user)
            if billing_obj:
                billing_obj.delete()
                response_dict["message"] = "Successfully delete address"
                response_dict["status"] = True
                return Response(response_dict, status=status.HTTP_200_OK)
            else:
                response_dict["error"] = "Billing details not found for this user"
                response_dict["status"] = False
                return Response(response_dict, status=status.HTTP_404_NOT_FOUND)
        else:
            response_dict["error"] = "Access Denied, Only Admin can access this"
            return Response(response_dict, status=status.HTTP_403_FORBIDDEN)
        
class CardDetailsCreateView(APIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (CustomTokenAuthentication,)

    def post(self, request):
        response_dict = {
            'status':True
        }
        serializer = CardDetailsSerializer(data=request.data)

        if request.user.user_type == 'ADMIN':
            if serializer.is_valid():
                card_details = serializer.save(user=request.user)
                response_dict = {
                    'id': card_details.id,
                    'user': card_details.user.id,
                    'holder_name': card_details.holder_name,
                    'card_number': card_details.card_number,
                    'expiration_date': card_details.expiration_date,
                    'ccv': card_details.ccv,
                }
                return Response(response_dict, status=status.HTTP_200_OK)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            response_dict["error"] = "Access Denied"
            return Response(response_dict,status=status.HTTP_403_FORBIDDEN)

        
class CardDetailsListView(APIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (CustomTokenAuthentication,)

    def get(self, request):
        response_dict = {'status':False}
        card_list = CardDetails.objects.filter(user=request.user)
        if request.user.user_type == "ADMIN":
            if card_list:
                response_dict["card_list"] = CardDetailsSerializer(card_list, context={'reqiest':request}, many=True).data
                response_dict["status"] = True
                return Response(response_dict, status=status.HTTP_200_OK)
            else:
                response_dict["card_list"] = CardDetailsSerializer(card_list, context={'reqiest':request}, many=True).data
                return Response(response_dict, status=status.HTTP_200_OK)
        else:
            response_dict["error"] = "Access Denied"
            return Response(response_dict,status=status.HTTP_403_FORBIDDEN)


class CardDetailsEdit(APIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (CustomTokenAuthentication,)

    def put(self, request, pk):
        admin_user = request.user
        
        if admin_user.user_type == 'ADMIN':
            card_obj = CardDetails.objects.get(id=pk, user=admin_user)

            if not card_obj:
                return Response({'error': 'Billing details not found for this user.'}, status=status.HTTP_404_NOT_FOUND)

            serializer = CardDetailsSerializer(card_obj, data=request.data, partial=True)

            if serializer.is_valid():
                card_detail = serializer.save()
                response_dict = {
                        'id': card_detail.id,
                        'user': card_detail.user.id,
                        'holder_name': card_detail.holder_name,
                        'card_number': card_detail.card_number,
                        'expiration_date': card_detail.expiration_date,
                        'ccv': card_detail.ccv,
                    }
                return Response(response_dict, status=status.HTTP_200_OK)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            response_dict["error"] = "Access Denied, Only admin can access this"
            return Response(response_dict, status=status.HTTP_403_FORBIDDEN)
        
    
class CardDetailsDelete(APIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (CustomTokenAuthentication,)

    def delete(self, request, pk):
        response_dict = {'status':False}
        
        if request.user.user_type == 'ADMIN':
            card_obj = CardDetails.objects.get(id=pk,  user=request.user)
            if card_obj:
                card_obj.delete()
                response_dict["status"] = True
                response_dict["message"] = "Successfull delete the card details"
                return Response(response_dict, status=status.HTTP_200_OK)
            else:
                response_dict["error"] = "Billing details not found for this user"
                return Response(response_dict, status=status.HTTP_400_BAD_REQUEST)
        else:
            response_dict["error"] = "Access Denied, Only Admin can access the process"
            return Response(response_dict, status=status.HTTP_403_FORBIDDEN)
        

class DeleteUser(APIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (CustomTokenAuthentication,)

    def delete(self, request):
        response_dict = {}
    
        try:
            user = request.user
            user_profile = UserProfile.objects.get(pk=user.id)

            user_profile.is_active = False
            user_profile.is_deleted = True
            user_email = user_profile.email + "deleted"
            user_profile.email = user_email
            user_profile.username = user_email
            user_profile.save()
            response_dict["status"] = True
            response_dict["message"] = "Successfully deleted the user"
            return Response(response_dict, status=status.HTTP_200_OK)
        except (TypeError, ValueError, OverflowError, UserProfile.DoesNotExist):
            response_dict["status"] = False
            response_dict["message"] = "Invalid token or user not found"
            return Response(response_dict, status=status.HTTP_400_BAD_REQUEST)
