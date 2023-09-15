from django.conf.urls import include
from user import api
from django.urls import path

urlpatterns = [
    path("login/", api.Applogin.as_view(), name="login"),
    path("verify-email/", api.VerifyEmail.as_view(), name="verify-email"),
    path("send-otp/", api.SendOtp.as_view(), name="send-otp"),
    path("verify-otp/", api.VerifyOtp.as_view(), name="verify-otp"),
    path("register-user/", api.RegisterUser.as_view(), name="register-user"),
    path("logout/", api.AppLogout.as_view(), name="logout"),
    path("set-password/", api.SetUserPassword.as_view(), name="set-password"),
    path("change-password/", api.ChangePassword.as_view(), name="change-password"),

    
    path('user-details/', api.UserDetail.as_view(), name='user')

]