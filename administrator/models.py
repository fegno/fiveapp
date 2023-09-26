from django.db import models
from user.models import UserProfile
from superadmin.models import BundleDetails, ModuleDetails

class SubscriptionDetails(models.Model):
    user = models.ForeignKey(
        UserProfile,
        blank=True,
        null=True,
        on_delete=models.CASCADE,   
        related_name="admin_subscriptions"
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
    received_amounts			=	models.FloatField(null=True,blank=True)
    payment_dates			=	models.DateTimeField(null=True,blank=True)
    
    status =	models.CharField(max_length=50,blank=True,null=False,db_index=True,choices=STATUS_CHOICES)
    is_active = models.BooleanField(null=False, blank=True, default=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)


class UploadedCsvFiles(models.Model):
    uploaded_by = models.ForeignKey(
        UserProfile,
        blank=True,
        null=True,
        on_delete=models.CASCADE,   
    )
    modules = models.ForeignKey(
        ModuleDetails,
        blank=True,
        null=True,
        on_delete=models.CASCADE,  
    )
    csv_file = models.FileField(null=True, blank=True)
    standard_working_hour = models.FloatField(null=True, blank=True, default=0)
    is_report_generated = models.BooleanField(null=False, blank=True, default=False)
    working_type = models.CharField(null=True, blank=True, max_length=1000)

    is_active = models.BooleanField(null=False, blank=True, default=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)


class CsvLogDetails(models.Model):
    uploaded_file = models.ForeignKey(
        UploadedCsvFiles,
        blank=True,
        null=True,
        on_delete=models.CASCADE,   
    )
    sl_no = models.CharField(null=True, blank=True, max_length=1000)
    employee_id = models.CharField(null=True, blank=True, max_length=1000)
    employee_name = models.CharField(null=True, blank=True, max_length=1000)
    department = models.CharField(null=True, blank=True, max_length=1000)
    team = models.CharField(null=True, blank=True, max_length=1000)
    designation = models.CharField(null=True, blank=True, max_length=1000)
    working_hour = models.FloatField(null=True, blank=True, default=0)
    extra_hour = models.FloatField(null=True, blank=True, default=0)

    is_active = models.BooleanField(null=False, blank=True, default=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)