from django.contrib import admin
from user.models import (
    UserProfile,
    Token,
    LoginOTP
)
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = UserProfile
        fields = ("username",)


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = UserProfile
        exclude = []


class CustomUserAdmin(UserAdmin):

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (
            _("Personal info"),
            {
                "fields": (
                    "email",
                    "first_name",
                    "free_subscription_start_date",
                    "free_subscription_end_date",
                    "available_free_users",
                    "take_free_subscription",
                    "free_subscribed"
                )
            },
        ),
        (
            _("Permissions"),
            {
                "fields": (
                    "user_type",
                    "is_active",
                    "is_superuser",
                )
            },
        ),
    )
    add_fieldsets = (
        (
            None,
            {"classes": ("wide",), "fields": ("username", "password1", "password2")},
        ),
    )
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm
    list_display = ("username", "first_name", "user_type")
    search_fields = ("username", "first_name")
    ordering = ("username",)



admin.site.register(UserProfile, CustomUserAdmin)
admin.site.register(Token)
admin.site.register(LoginOTP)

