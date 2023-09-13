from django.shortcuts import render
from django.views import View
from django.shortcuts import render, redirect
import random, string
import json, os
from datetime import timedelta, date, datetime
from django.db import transaction

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
