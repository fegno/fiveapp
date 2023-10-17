from django.db import models
from user.models import UserProfile, BillingDetails, CardDetails
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
    bill = models.ForeignKey(
        BillingDetails,
        blank=True,
        null=True,
        on_delete=models.CASCADE,   
    )
    card = models.ForeignKey(
        CardDetails,
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
    custom_request = models.CharField(null=True, blank=True, max_length=1000)

    total_price = models.FloatField(
        null=False, blank=False, default=0
    )
    received_amounts			=	models.FloatField(null=True,blank=True)
    payment_dates			=	models.DateTimeField(null=True,blank=True)
    parchase_user_type		=	models.CharField(null=True,blank=True,max_length=255, default="Subscription")
    user_count              = models.IntegerField(null=True, blank=True)
    status =	models.CharField(max_length=50,blank=True,null=False,db_index=True,choices=STATUS_CHOICES)
    
    
    company_name = models.CharField(max_length=150, null=True, blank=True)
    address = models.TextField(max_length=1000, null=True, blank=True)
    billing_contact = models.CharField(max_length=100, null=True, blank=True)
    issuing_country = models.CharField(max_length=100, null=True, blank=True)
    legal_company_name = models.CharField(max_length=100, null=True, blank=True)
    tax_id = models.CharField(max_length=12, null=True, blank=True)
    holder_name = models.CharField(max_length=100, null=True, blank=True)
    card_number = models.CharField(max_length=20, null=True, blank=True)
    expiration_date = models.CharField(max_length=5, null=True, blank=True)
    ccv = models.CharField(max_length=3, null=True, blank=True)

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
    monthly_revenue = models.FloatField(null=True, blank=True, default=0)
    total_working_days = models.FloatField(null=True, blank=True, default=0)

    company_target_achieved = models.FloatField(null=True, blank=True, default=0)
    department_target_achieved = models.FloatField(null=True, blank=True, default=0)
    company_varriable_pay_wgt = models.FloatField(null=True, blank=True, default=0)
    department_varriable_pay_wgt = models.FloatField(null=True, blank=True, default=0)
    individual_varriable_pay_wgt = models.FloatField(null=True, blank=True, default=0)

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
    absent_days = models.FloatField(null=True, blank=True, default=0)

    hourly_rate = models.FloatField(null=True, blank=True, default=0)
    total_pay = models.FloatField(null=True, blank=True, default=0)
    fixed_pay = models.FloatField(null=True, blank=True, default=0)
    individual_ach_in = models.FloatField(null=True, blank=True, default=0)
    gross_pay = models.FloatField(null=True, blank=True, default=0)
    varriable_pay = models.FloatField(null=True, blank=True, default=0)
    overtime_pay = models.FloatField(null=True, blank=True, default=0)
    no_of_holiday = models.FloatField(null=True, blank=True, default=0)
    holiday_hours = models.FloatField(null=True, blank=True, default=0)
    holiday_pay = models.FloatField(null=True, blank=True, default=0)
    individual_varriable_pay = models.FloatField(null=True, blank=True, default=0)
    department_varriable_pay = models.FloatField(null=True, blank=True, default=0)
    company_varriable_pay = models.FloatField(null=True, blank=True, default=0)

    is_active = models.BooleanField(null=False, blank=True, default=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)


class DepartmentWeightage(models.Model):
    uploaded_file = models.ForeignKey(UploadedCsvFiles, on_delete=models.CASCADE, null=True, blank=True)
    percentage = models.FloatField(null=True, blank=True, default=0)
    department = models.CharField(null=True, blank=True, max_length=1000)

    is_active = models.BooleanField(default=False, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now_add=True)


class AddToCart(models.Model):
    added_by = models.ForeignKey(UserProfile, on_delete=models.CASCADE, null=True, blank=True)
    count = models.IntegerField(default=1, null=True, blank=True)
    amount = models.FloatField(default=0, null=True, blank=True)

    is_active = models.BooleanField(default=False, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now_add=True)


class CustomRequest(models.Model):
    user = models.ForeignKey(
        UserProfile,
        blank=True,
        null=True,
        on_delete=models.CASCADE,   
    )
    name = models.CharField(null=True, blank=True, max_length=1000)
    email = models.CharField(null=True, blank=True, max_length=1000)
    phone = models.CharField(null=True, blank=True, max_length=1000)

    module = models.ManyToManyField(ModuleDetails, blank=True)
    bundle = models.ManyToManyField(BundleDetails, blank=True)
    subscription_start_date = models.DateField(null=True, blank=True)
    subscription_end_date = models.DateField(null=True, blank=True)
    is_subscribed = models.BooleanField(null=False, blank=True, default=True)
    subscription_type = models.CharField(null=True, blank=True, max_length=1000)
    total_price = models.FloatField(
        null=False, blank=False, default=0
    )
    status = models.CharField(null=True, blank=True, max_length=1000, default="Pending")
   
    is_active = models.BooleanField(null=False, blank=True, default=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
