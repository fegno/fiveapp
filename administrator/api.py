from django.shortcuts import render
from rest_framework.response import Response
from superadmin.models import ModuleDetails, BundleDetails
from rest_framework.permissions import AllowAny, IsAuthenticated
from user.api_permissions import CustomTokenAuthentication
from rest_framework.views import APIView
from rest_framework import status
from datetime import datetime
from django.utils import timezone
from administrator.serializers import ModuleDetailsSerializer, BundleDetailsSerializer

class Homepage(APIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (CustomTokenAuthentication,)

    def get(self, request):
        response_dict = {"status": False}
        user = request.user
        if user.user_type == "ADMIN":
            if user.take_free_subscription:
                current_datetime = timezone.now().date()
                if user.free_subscription_end_date and user.free_subscription_end_date > current_datetime:
                    modules = ModuleDetails.objects.filter(is_active=True)
                    bundles = BundleDetails.objects.filter(is_active=True)
                    response_dict["bundles"] = BundleDetailsSerializer(bundles,context={"request": request}, many=True).data
                    response_dict["modules"] = ModuleDetailsSerializer(modules,context={"request": request}, many=True,).data
                    response_dict["status"] = True
                    return Response(response_dict, status=status.HTTP_200_OK)
                else:
                    response_dict["error"] = "Access denied. Your Free subscription has expired"
                    return Response(response_dict, status=status.HTTP_403_FORBIDDEN)
            else:
                response_dict["error"] = "Not started your Free subscription"
                return Response(response_dict, status=status.HTTP_403_FORBIDDEN)
        else:
            response_dict["error"] = "Access denied, Only Admin can access the module list"
            return Response(response_dict, status=status.HTTP_403_FORBIDDEN)
        
