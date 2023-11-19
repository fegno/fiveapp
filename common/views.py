import re
from django.shortcuts import get_object_or_404, render
from django.views import View
from django.shortcuts import render, redirect
import random, string
import json, os
from datetime import timedelta, date, datetime
from django.db import transaction
from superadmin.models import InviteDetails, UserAssignedModules
from user.models import LoginOTP, UserProfile, Token
from django.templatetags.static import static
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK
import datetime
from django.contrib.auth import authenticate, login, logout as auth_logout
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from fiveapp.utils import get_error
from administrator.models import UserSubscriptionDetails

class Login(View):
    def get(self, request):
        landing_page_urls = {
            "SUPER_ADMIN": "superadmin:landing-page",
        }
        response_dict = {}
        if not request.session.get("token"):
            response_dict = {}
            return render(request, "public/login.html", response_dict)
        else:
            user_type = request.session.get("data").get("user_type")
            return redirect(landing_page_urls[user_type])

    def post(self, request):
        user_type = ""
        response_dict = {"success": False}
        landing_page_url = {
            "SUPER_ADMIN": "superadmin:landing-page",
        }
        username = request.POST.get("username")
        password = request.POST.get("password")
        authenticated = authenticate(username=username, password=password)
        try:
            user = UserProfile.objects.get(username=username)
        except UserProfile.DoesNotExist:
            response_dict[
                "reason"
            ] = "No account found for this username. Please signup."
            messages.error(request, response_dict["reason"])
        if not authenticated:
            response_dict["reason"] = "Invalid credentials."
            messages.error(request, response_dict["reason"])
            return redirect(request.GET.get("from") or "user:login")

        else:
            session_dict = {"real_user": authenticated.id}
            token, c = Token.objects.get_or_create(
                user=user, defaults={"session_dict": json.dumps(session_dict)}
            )

            user_type = authenticated.user_type
            request.session["data"] = {
                "user_id": user.id,
                "user_type": user.user_type,
                "token": token.key,
                "username": user.username,
                "status": user.is_active,
            }

            request.session["user"] = authenticated.username
            request.session["token"] = token.key
            request.session["status"] = user.is_active
            return redirect(landing_page_url[user_type])
        

class AcceptReject(View):

    def get(self, request, user_invite_id):
        response_dict = {}

        invited_user = get_object_or_404(InviteDetails, id=user_invite_id)
        if invited_user.is_verified:
            response_dict["message"] = "The User with the link is already verified"
        elif invited_user.is_reject:
            response_dict["message"] = "The link is rejected"
        elif invited_user.is_deleted:
            response_dict["message"] = "The user is deleted"

        context = {
            'invited_user': invited_user,
            'message': response_dict.get("message", ""),
            'password_errors': "",
        }

        return render(request, 'verify_link.html', context)
    
    def post(self, request, user_invite_id):
        response_dict = {}
        invited_user = get_object_or_404(InviteDetails, id=user_invite_id)

        if invited_user.is_verified:
            response_dict["message"] = "User is already verified"
        elif invited_user.is_reject:
            response_dict["message"] = "The user is rejected"
        elif invited_user.is_deleted:
            response_dict["message"] = "The user is deleted"
        else:
            if 'reject' in request.POST:
                invited_user.is_reject = True
                invited_user.save()
                created_admin = invited_user.user
                if invited_user.is_free_user:
                    created_admin.available_free_users += 1
                else:
                    created_admin.available_paid_users += 1
                created_admin.save()
                response_dict["message"] = "User deleted from invitation" 
                
            elif 'set_password' in request.POST:
                password = request.POST.get('password')
                c_password = request.POST.get('c-password')

                errors=[]

                if len(password) < 5:
                    errors.append("Password must have at least 5 characters.")
                if not re.search("[a-zA-Z]", password):
                    errors.append("Password must contain at least one letter.")
                if not re.search("[0-9]", password):
                    errors.append("Password must contain at least one number.")
                if password != c_password:
                    errors.append("Passwords do not match.")

                if errors:
                    context = {
                        'invited_user': invited_user,
                        'message': "",
                        'password_errors': ", ".join(errors),
                    }
                    return render(request, 'verify_link.html', context)

                admin_subscription = UserSubscriptionDetails.objects.filter(
                    user=invited_user.user, 
                ).last()
                if c_password == password:
                    invited_user.is_verified = True
                    invited_user.save()
                    new_user = UserProfile.objects.create(
                        user_type="USER",
                        username=invited_user.email,
                        email=invited_user.email,
                        first_name=invited_user.name,
                        password=make_password(password),
                        created_admin=invited_user.user,
                        is_free_user=invited_user.is_free_user
                    )
                    if admin_subscription and not new_user.is_free_user:
                        new_user.subscription_start_date = admin_subscription.subscription_start_date
                        new_user.subscription_end_date = admin_subscription.subscription_end_date
                        new_user.save()

                    assigned_modules = invited_user.module.all()
                    user_assigned_module = UserAssignedModules.objects.create(user=new_user)
                    user_assigned_module.module.set(assigned_modules)

                    otp_value = random.randint(100000, 999999)
                    login_otp = LoginOTP.objects.create(
                        email=new_user.email,
                        otp=otp_value,
                        is_verified=True,
                        user_type="USER"
                    )
                    response_dict["message"] = "Password set successfully"
                    
                else:
                    response_dict["message"] = "Password not match"

            context = {
                'invited_user': invited_user,
                'message': response_dict.get("message", ""),
                'password_errors': "",
            }

        return render(request, 'verify_link.html', context)
