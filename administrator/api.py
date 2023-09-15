from django.shortcuts import render
from rest_framework.response import Response
from superadmin.models import ModuleDetails
from rest_framework.permissions import AllowAny, IsAuthenticated
from user.api_permissions import CustomTokenAuthentication
from rest_framework.views import APIView
from rest_framework import status
from datetime import datetime
from django.utils import timezone

class ModuleDetailsList(APIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (CustomTokenAuthentication,)

    def get(self, request):
        user = request.user
        if user.user_type == "ADMIN":
            if user.take_free_subscription:
                current_datetime = timezone.now()
                if user.free_subscription_end_date and user.free_subscription_end_date > current_datetime:
                    modules = ModuleDetails.objects.all()
                    module_data = [{"id": module.id, "name": module.title} for module in modules]
                    return Response({"modules": module_data}, status=status.HTTP_200_OK)
                else:
                    return Response({"error": "Access denied. Your Free subscription has expired"}, status=status.HTTP_403_FORBIDDEN)
            else:
                return Response({"error": "Not started your Free subscription"}, status=status.HTTP_403_FORBIDDEN)
        else:
            return Response({"error": "Access denied, Only Admin can access the module list"}, status=status.HTTP_403_FORBIDDEN)
        
        



