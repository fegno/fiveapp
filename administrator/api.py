from django.shortcuts import render
from rest_framework.response import Response
from rest_framework import generics
from superadmin.models import ModuleDetails
from user.models import UserProfile
from .serializers import ModuleDetailsSerializer
from rest_framework.permissions import AllowAny, IsAuthenticated
from user.api_permissions import CustomTokenAuthentication
from rest_framework.views import APIView
from rest_framework import status

class ModuleDetailsList(generics.ListCreateAPIView):
    permission_classes = (AllowAny,)

    queryset = ModuleDetails.objects.all()
    serializer_class = ModuleDetailsSerializer



