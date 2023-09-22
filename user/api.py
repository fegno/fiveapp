import re
import string
import random
from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.contrib.auth import authenticate
from django.templatetags.static import static
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from django.contrib.auth import login, logout

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

from user.models import UserProfile, Token, LoginOTP
from user.serializers import RegisterSerializer, UserSerializer
from user.task import send_mail
from rest_framework import status
from django.core.mail import send_mail, EmailMessage
from django.template.loader import render_to_string


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
            authenticated = authenticate(username=email, password=password)
            if authenticated:
                user = get_object_or_404(UserProfile, username=email)
                user.save()
                flag = 1
            else:
                response_dict["message"] = "Username or password incorrect"
                return Response(response_dict, HTTP_200_OK)
        else:
            response_dict["message"] = "Login Method DoesNotExist"
            return Response(response_dict, HTTP_200_OK)
       
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
            response_dict["error"] = "Email already added"
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
        with transaction.atomic():
            if serializer.is_valid():
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
        return Response(response_dict, HTTP_200_OK)


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
        if new_password != confirm_password:
            response_dict["error"] = "Password does not match"
        user = UserProfile.objects.filter(username=email).first()
        user.set_password(new_password)
        user.save()
        response_dict["status"] = True
        response_dict["message"] = "Password created"
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
        if new_password != confirm_password:
            response_dict["error"] = "Password does not match"
            return Response(response_dict, HTTP_200_OK)
        if not user.check_password(old_password):
            response_dict["error"] = "Old Password is incorrect"
            return Response(response_dict, HTTP_200_OK)
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
        user_profile = UserProfile.objects.filter(id=user.id).update(first_name=first_name, last_name=last_name)
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
        company = UserProfile.objects.filter(id=user.id).update(company_name=company_name)
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
        email_exist = UserProfile.objects.filter(email=email).exists()
        if email_exist:
            response_dict["error"] = "The email already in use"
            return Response(response_dict, HTTP_200_OK)
        elif user.username == email:
            response_dict["error"] = "The email already used as username"
            return Response(response_dict, HTTP_200_OK)
        user.email = email
        user.username = email
        user.save()
        response_dict["message"] = "The email was successfully updated"
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
        if user and user.user_type == "ADMIN":
            response_dict["user_type"] = "ADMIN"
            response_dict["password_set"] = True
        elif user:
            if user.password:
                response_dict["password_set"] = True
                response_dict["user_type"] = "USER"
            else:
                response_dict["password_set"] = False
                response_dict["user_type"] = "USER"
        elif not user:
            if LoginOTP.objects.filter(email=email, is_verified=True):
                otp_user = LoginOTP.objects.filter(email=email)
                response_dict["password_set"] = False
                response_dict["user_type"] = otp_user.user_type
            else:
                response_dict["user_type"] = "Not Registered"
                response_dict["password_set"] = False

        response_dict["status"] = True
        return Response(response_dict, status=status.HTTP_200_OK)