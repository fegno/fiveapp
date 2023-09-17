from django.db import models
from user.models import UserProfile
from superadmin.models import BundleDetails, ModuleDetails

class SubscriptionDetails(models.Model):
    user = models.ForeignKey(
        UserProfile,
        blank=True,
        null=True,
        on_delete=models.CASCADE,   
    )
    module = models.ManyToManyField(ModuleDetails, blank=True)
    bundle = models.ManyToManyField(BundleDetails, blank=True)
    subscription_start_date = models.DateField(null=True, blank=True)
    subscription_end_date = models.DateField(null=True, blank=True)
    is_subscribed = models.BooleanField(null=False, blank=True, default=True)
    subscription_type = models.CharField(null=True, blank=True, max_length=1000)

    is_active = models.BooleanField(null=False, blank=True, default=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

STATUS_CHOICES=(   
	('Pending','Pending'),
	('Placed','Placed'),
)
class PurchaseDetails(models.Model):
    user = models.ForeignKey(
        UserProfile,
        blank=True,
        null=True,
        on_delete=models.CASCADE,   
    )
    module = models.ManyToManyField(ModuleDetails, blank=True)
    bundle = models.ManyToManyField(BundleDetails, blank=True)
    subscription_start_date = models.DateField(null=True, blank=True)
    subscription_end_date = models.DateField(null=True, blank=True)
    is_subscribed = models.BooleanField(null=False, blank=True, default=True)
    subscription_type = models.CharField(null=True, blank=True, max_length=1000)
    total_price = models.FloatField(
        null=False, blank=False, default=0
    )
    status =	models.CharField(max_length=50,blank=True,null=False,db_index=True,choices=STATUS_CHOICES)
    is_active = models.BooleanField(null=False, blank=True, default=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

class UserAssignedModules(models.Model):
    user = models.ForeignKey(
        UserProfile,
        blank=True,
        null=True,
        on_delete=models.CASCADE,   
    )
    module = models.ManyToManyField(ModuleDetails, blank=True)   
    is_active = models.BooleanField(null=False, blank=True, default=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
