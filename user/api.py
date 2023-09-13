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
from user.serializers import RegisterSerializer
from user.task import send_mail


def process_tasks():
    process_tasks_cmd = "python manage.py process_tasks"
    process_tasks_args = shlex.split(process_tasks_cmd)
    process_tasks_subprocess = subprocess.Popen(process_tasks_args)


def random_otp_generator(size=6, chars="123456789"):
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
                'user_type':user.user_type
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
            response_dict["reason"] = "Email already added"
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
            otp=otp
        )
        process_tasks()
        send_mail(otp, request.data.get("email"))
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
            response_dict["message"] = "Success"
            response_dict["status"] = True
        else:
            response_dict["reason"] = "OTP incorrect"
            response_dict["status"] = False
        return Response(response_dict, HTTP_200_OK)


class RegisterUser(APIView):
    permission_classes = (AllowAny,)
    authentication_classes = tuple()

    def post(self, request):
        response_dict = {"status": False}
        data = request.data   
        serializer = RegisterSerializer(data=data)
        if UserProfile.objects.filter(
            email=data.get("email"),
        ).first():
            response_dict["reason"] ="User already exists"
            return Response(response_dict, HTTP_200_OK)
        with transaction.atomic():
            if serializer.is_valid():
                user = serializer.save(
                    user_type="ADMIN",
                )
                user.username = user.email
                user.set_password(data.get("password"))
                user.save()
                response_dict["status"] = True
                response_dict["message"] = "Registered successfully"
            else:
                response_dict["reason"] = get_error(serializer)
        return Response(response_dict, HTTP_200_OK)


class AppLogout(APIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (CustomTokenAuthentication,)

    def post(self, request):
        logout(request)
        response_dict = {"status": True}
        return Response(response_dict, HTTP_200_OK)
