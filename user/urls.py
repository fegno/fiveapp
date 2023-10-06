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
    path("login-method-check/", api.CheckLoginMethod.as_view(), name="login"),

    
    path('user-details/', api.UserDetail.as_view(), name='user'),
    path("change-name/", api.ChangeName.as_view(), name="change-name"),
    path("change-company-name/", api.ChangeComapnyName.as_view(), name="change-company-name"),
    path("change-email/", api.ChangeEmail.as_view(), name="change-email"),


    path("billing-details-create/", api.BillingDetailsCreateView.as_view(), name="billing-details-create"),
    path("billing-details-list/", api.BillingDetailsListView.as_view(), name="billing-details-list"),

    path("card-details-create/", api.CardDetailsCreateView.as_view(), name='card-details-create'),
    path("card-details-list/", api.CardDetailsListView.as_view(), name="card-details-list"),

]