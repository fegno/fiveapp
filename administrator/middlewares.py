from django.shortcuts import get_object_or_404
from datetime import date, datetime, timedelta
from user.models import UserProfile
from django.utils import timezone
from administrator.models import PurchaseDetails, SubscriptionDetails
from superadmin.models import FreeSubscriptionDetails

class SubscriptionMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.user.is_authenticated:
            if request.user.user_type == "ADMIN":
                user = request.user
                free_subscribed_modules = FreeSubscriptionDetails.objects.filter(
                    user=request.user,
                    free_subscription_end_date__gte=timezone.now().date()
                )
                if not free_subscribed_modules:
                    user.free_subscribed = False
                    user.save()
                subscription = SubscriptionDetails.objects.filter(
                    user=user, 
                    is_subscribed=True
                ).last()
                if subscription and subscription.subscription_end_date < timezone.now().date():
                    subscription.is_subscribed = False
                    user.is_subscribed = False
                    user.save()
                    subscription.save()
                
        return response