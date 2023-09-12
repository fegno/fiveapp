from rest_framework import permissions
from datetime import datetime
from django.conf import settings
from rest_framework.authentication import (
    TokenAuthentication,
    SessionAuthentication,
    BaseAuthentication,
)
import random, string
import json
from django.db import models
from user.models import UserProfile, Token


class CustomTokenAuthentication(BaseAuthentication):
    def authenticate(self, request):
        token_auth = TokenAuthentication()
        token_auth.model = Token
        token_response = token_auth.authenticate(request)
        if settings.DISABLE_INTERNAL_REQUEST_CALL_API:
            session_response = None
            try:
                session_response = SessionAuthentication().authenticate(request)
            except Exception:  # Can't take any chances. Catch-all
                print("SessionAuthentication Exception Swallowed")
            return token_response or session_response
        return token_response


def is_expired(token):
    return False
    # @TODO: remove above line
    if not token:
        return True
    naive = token.created
    naive = naive.replace(tzinfo=None)
    res = (datetime.now() - naive).total_seconds() > settings.MAX_INACTIVE_TIME
    if res:
        token.delete()
    return res


class CommonPermission(permissions.BasePermission):
    message = "You are not authorized for this action."

    def has_permission(self, request, view):
        if is_expired(request.auth) or not request.user.is_authenticated:
            return False
        return self.check_perm(request, view)

    def check_perm(self, request, view):
        raise NotImplementedError("Not implemented")


class IsSuperAdmin(CommonPermission):
    def check_perm(self, request, view):
        return request.user.user_type == "SUPER_ADMIN"


class IsAdmin(CommonPermission):
    def check_perm(self, request, view):
        return request.user.user_type == "ADMIN"
