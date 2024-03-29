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
    path("forgot-password-otp/", api.ForgotPasswordOtp.as_view(), name="forgot-password-otp"),
    path("forgot-password-verify-otp/", api.ForgotVerifyOtp.as_view(), name="forgot-password-verify-otp"),
    path("forgot-password-change/", api.ForgotPassword.as_view(), name="forgot-password-change"),

    path('user-details/', api.UserDetail.as_view(), name='user'),
    path("change-name/", api.ChangeName.as_view(), name="change-name"),
    path("change-company-name/", api.ChangeComapnyName.as_view(), name="change-company-name"),
    path("change-email/", api.ChangeEmail.as_view(), name="change-email"),
    path("update-email/", api.UpdateEmail.as_view(), name='update-email'),

    path("billing-details-create/", api.BillingDetailsCreateView.as_view(), name="billing-details-create"),
    path("billing-details-list/", api.BillingDetailsListView.as_view(), name="billing-details-list"),
    path("billing-details-edit/<int:pk>/", api.BillingDetailsEdit.as_view(), name='billing-edit'),
    path("billing-details-delete/<int:pk>/", api.BillingDetailsDelete.as_view(), name='billing-details-delete'),

    path("card-details-create/", api.CardDetailsCreateView.as_view(), name='card-details-create'),
    path("card-details-list/", api.CardDetailsListView.as_view(), name="card-details-list"),
    path("card-details-edit/<int:pk>/", api.CardDetailsEdit.as_view(), name='card-edit'),
    path("card-details-delete/<int:pk>/", api.CardDetailsDelete.as_view(), name="card-details-delete"),

    path("delete-user/", api.DeleteUser.as_view(), name="card-details-delete")

]