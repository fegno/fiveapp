from rest_framework import serializers
from user.models import UserProfile
from django.utils import timezone

class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = (
            "first_name",
            "mobile_no",
            "last_name",
            "email",
            "company_name",
            "industrial_size",
            "employee_position",
        )

class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserProfile
        fields = (
            "first_name",
            "last_name",
            "mobile_no",
            "email",
            "company_name",
            "industrial_size",
            "employee_position",
            "created",
            "user_type",
            "free_subscription_start_date",
            "free_subscription_end_date",
            "free_subscribed",
            "take_free_subscription",
            "available_free_users",
            "is_subscribed",
            "is_free_user",
            "available_paid_users",
            "total_users",
        )
    def to_representation(self, obj, *args, **kwargs):
        cd = super(UserSerializer, self).to_representation(
            obj, *args, **kwargs
        )
        if obj.free_subscription_end_date and obj.free_subscription_end_date > timezone.now().date():
            days = obj.free_subscription_end_date - obj.free_subscription_start_date
            cd["free_expire_in"] = days.days
        return cd
