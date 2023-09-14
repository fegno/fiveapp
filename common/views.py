from django.shortcuts import render
from django.views import View
from django.shortcuts import render, redirect
import random, string
import json, os
from datetime import timedelta, date, datetime
from django.db import transaction
from user.models import UserProfile, Token
from django.templatetags.static import static
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK
import datetime
from django.contrib.auth import authenticate, login, logout as auth_logout
from django.contrib import messages

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