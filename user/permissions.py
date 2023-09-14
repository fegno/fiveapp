from django.contrib.auth.mixins import AccessMixin
from django.urls import reverse
from django.conf import settings
from django.shortcuts import redirect
from django.contrib import messages


class UserTypeTestMixin(AccessMixin):
    user_type = None
    session_data = None

    user_type_home_page = {
        "SUPER_ADMIN": "superadmin:landing-page",
    }
    permission_denied_message = "You are not allowed there!"

    def test_func(self):
        raise NotImplementedError(
            "{0} is missing the implementation of the test_func() method.".format(
                self.__class__.__name__
            )
        )

    def get_login_url(self):
        login_url = self.login_url or settings.LOGIN_URL
        if not self.session_data:
            return login_url
        else:
            if self.user_type:
                return reverse(self.user_type_home_page[self.user_type])
            return login_url

    def dispatch(self, request, *args, **kwargs):
        self.session_data = request.session.get("data", None)
        if self.session_data:
            self.user_type = self.session_data.get("user_type")

        else:
            return self.handle_no_permission()

        user_test_result = self.test_func()
        if not user_test_result:
            messages.error(request, "You are not allowed here")
            return self.handle_no_permission()
        dispatched = super(UserTypeTestMixin, self).dispatch(request, *args, **kwargs)
        if getattr(request, "token_expired", False):
            request.session.flush()
            self.session_data = None
            self.user_type = None
            self.login_url = "/"
            return self.handle_no_permission()
        return dispatched


class IsAdminMixin(UserTypeTestMixin):
    def test_func(self):
        return self.user_type == "ADMIN"


class IsSuperAdminMixin(UserTypeTestMixin):
    def test_func(self):
        return self.user_type == "SUPER_ADMIN"



class UserStatusTestMixin(AccessMixin):
    def test(self):
        raise NotImplementedError(
            "{0} is missing the implementation of the test_func() method.".format(
                self.__class__.__name__
            )
        )

    login_url = "/"
    permission_denied_message = "Your account is not active!"

    def dispatch(self, request, *args, **kwargs):
        self.session_data = request.session.get("data", None)
        user_test_result = self.test()
        dispatched = super(UserStatusTestMixin, self).dispatch(request, *args, **kwargs)
        if getattr(request, "token_expired", False):
            request.session.flush()
            self.session_data = None
            return self.handle_no_permission()
        return dispatched

