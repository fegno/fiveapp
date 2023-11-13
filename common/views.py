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
            response_dict["message"] = "The User with the linke is already verified"
        elif invited_user.is_reject:
            response_dict["message"] = "The link is rejected"
        elif invited_user.is_deleted:
            response_dict["message"] = "The user is deleted"
        
        return render(request, 'verify_link.html', response_dict)
    
    def post(self, request, user_invite_id):
        response_dict ={}
        invited_user = get_object_or_404(InviteDetails, id=user_invite_id)
        print(invited_user)

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
                print(created_admin)
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
                    response_dict["message"] = ", ".join(errors)
                    

                if c_password == password:
                    invited_user.is_verified = True
                    invited_user.save()
                    new_user = UserProfile.objects.create(user_type="USER", username=invited_user.email, email=invited_user.email, first_name=invited_user.name, password=make_password(password), created_admin=invited_user.user, is_free_user=invited_user.is_free_user)

                    assigned_modules = invited_user.module.all()
                    user_assigned_module = UserAssignedModules.objects.create(user=new_user)
                    user_assigned_module.module.set(assigned_modules)

                    otp_value = random.randint(100000, 999999)
                    login_otp = LoginOTP.objects.create(
                        email=new_user.email,
                        otp=otp_value,
                        is_verified=True
                    )
                    response_dict["message"] = "Password set successfully"
                else:
                    response_dict["message"] = "Password not match"
            return render(request, 'verify_link.html', response_dict)
        return render(request, 'verify_link.html', response_dict)
    
# class AcceptReject(APIView):
#     permission_classes = (AllowAny,)

#     def post(self, request, user_invite_id):

#         response_dict = {}
#         invite_user = get_object_or_404(InviteDetails, id=user_invite_id)

#         email = invite_user.email
        
#         if invite_user.is_verified:
#             return Response({"message": "The user is already verified"}, status=status.HTTP_400_BAD_REQUEST)
#         elif invite_user.is_reject:

#             return Response({"message": "The user is rejected"}, status=status.HTTP_400_BAD_REQUEST)
#         elif invite_user.is_deleted:
#             return Response({"message": "The user is deleted"}, status=status.HTTP_400_BAD_REQUEST)
#         else:
#             rejection_button_click = request.data.get('rejection_button_click')

#             if rejection_button_click:
#                 invite_user.is_reject=True
#                 invited_admin_obj = UserProfile.objects.get(email=email)
#                 print(invited_admin_obj)
#                 invited_admin = invited_admin_obj.created_admin
#                 print(invited_admin, '12345')
#                 if invite_user.user.is_free_user:
                    
#                     invited_admin.available_free_users += 1
#                     invited_admin.save()
#                 else:
#                     invited_admin.available_paid_users += 1
#                     invited_admin.save()
#                 user_profile = UserProfile.objects.get(email=email).delete() 
#                 response_dict["message"] = "User deleted from invitation"  

#             else:
#                 password = request.data.get('password')
#                 confirm_password = request.data.get('confirm_password')

#                 if password != confirm_password:
#                     return Response({"message": "Password and confirm password do not match"}, status=status.HTTP_400_BAD_REQUEST)
#                 elif len(password) < 5:
#                     return Response({"message": "Password must be at least 8 characters long"}, status=status.HTTP_400_BAD_REQUEST)
#                 else:
#                     user_profile = UserProfile.objects.get(email=email)
#                     user_profile.is_active = True
#                     invite_user.is_verified = True
#                     invite_user.save()

#                     # Return success response
#                     response_dict["message"] = "Account created"
#                     return Response(response_dict, status=status.HTTP_201_CREATED)
#             return Response(response_dict, status=status.HTTP_200_OK)
#         return Response(response_dict, status=status.HTTP_200_OK)