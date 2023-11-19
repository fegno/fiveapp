from rest_framework import serializers
from user.models import CardDetails, UserProfile, BillingDetails
from django.utils import timezone
from administrator.models import PurchaseDetails, SubscriptionDetails

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
            "id",
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
            days = obj.free_subscription_end_date -timezone.now().date() 
            cd["free_expire_in"] = days.days
        subscription = SubscriptionDetails.objects.filter(
			user=obj, 
		).last()
        if obj.user_type == "USER":
            cd["user_expired"] = False
            if obj.subscription_end_date and obj.subscription_end_date < timezone.now().date():
                cd["user_expired"] = True
            cd["subscription_start_date"] = obj.subscription_start_date
            cd["subscription_end_date"] = obj.subscription_end_date
            if obj.subscription_start_date:
                days = obj.subscription_end_date  - timezone.now().date()
                cd["subscription_expire_in"] = days.days
        if subscription and obj.user_type != "USER":
            cd["subscription_type"] = subscription.subscription_type
            cd["subscription_start_date"] = subscription.subscription_start_date
            cd["subscription_end_date"] = subscription.subscription_end_date
            if subscription.is_subscribed:
                days = subscription.subscription_end_date  - timezone.now().date()
                cd["subscription_expire_in"] = days.days

        return cd



class BillingDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = BillingDetails
        fields = (
            'id',
            'company_name', 
            'address', 
            'billing_contact',
            'issuing_country',
            'legal_company_name',
            'tax_id'
        )


class CardDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CardDetails
        fields = (
            'id',
            'holder_name',
            'card_number',
            'expiration_date',
            'ccv'
        )
