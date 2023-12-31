from django.db import models
from user.models import UserProfile

Type_Choice = (
    ("Team Indicator", "Team Indicator"),
    ("Team Workforce Plan Corporate", "Team Workforce Plan Corporate"),
    ("Team Cost", "Team Cost"),
    ("Payroll Analytics", "Payroll Analytics"),
    ("Gender Analytics", "Gender Analytics"),
    ("Utility Meter","Utility Meter"),
    ("Sale Center","Sale Center"),
    ("Support","Support"),
    ("Impression","Impression"),
    ("Metrics Meter","Metrics Meter"),
    ("Warehouse MAP Retailing","Warehouse MAP Retailing"),
    ("Logistic Controller","Logistic Controller"),
    ("Odometers","Odometers")
)


class ModuleDetails(models.Model):
    department = models.CharField(null=True, blank=True, max_length=100)
    title = models.CharField(null=True, blank=True, max_length=1000, choices=Type_Choice,)
    description = models.TextField(null=True, blank=True)
    bundle_name = models.TextField(null=True, blank=True)
    csv_file = models.FileField(null=True, blank=True)
    position = models.IntegerField(default=0)
    module_identifier = models.IntegerField(default=0)

    weekly_price = models.FloatField(
        null=True, blank=True, default=0
    )
    monthly_price = models.FloatField(
       null=True, blank=True, default=0
    )
    yearly_price = models.FloatField(
        null=True, blank=True, default=0
    )
    modules = models.ForeignKey(
        'self',
        blank=True,
        null=True,
        on_delete=models.CASCADE,   
    )
    is_submodule = models.BooleanField(null=False, blank=True, default=False)
    is_active = models.BooleanField(null=False, blank=True, default=True)
    created = models.DateTimeField(auto_now_add=True)

class FeatureDetails(models.Model):
    feature = models.TextField(null=True, blank=True)
    benifit = models.TextField(null=True, blank=True)
    modules = models.ForeignKey(
        "ModuleDetails",
        blank=True,
        null=True,
        on_delete=models.CASCADE,  
    )

    is_active = models.BooleanField(null=False, blank=True, default=True)
    created = models.DateTimeField(auto_now_add=True)


class BundleDetails(models.Model):
    title = models.CharField(null=True, blank=True, max_length=1000)
    modules = models.ManyToManyField(
        "ModuleDetails",
        blank=True   
    )
    weekly_price = models.FloatField(
       null=False, blank=False, default=0
    )
    monthly_price = models.FloatField(
        null=False, blank=False, default=0
    )
    yearly_price = models.FloatField(
        null=False, blank=False, default=0
    )
    icon = models.FileField(null=True, blank=True)

    is_active = models.BooleanField(null=False, blank=True, default=True)
    created = models.DateTimeField(auto_now_add=True)

class ModuleReports(models.Model):
    module = models.ForeignKey(
        ModuleDetails,
        blank=True,
        null=True,
        on_delete=models.CASCADE,   
    )
    report = models.TextField(null=True, blank=True)

    is_active = models.BooleanField(null=False, blank=True, default=True)
    created = models.DateTimeField(auto_now_add=True)

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


class DeleteUsersLog(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, null=True, blank=True, related_name='deleted_user_log')
    module = models.ManyToManyField(ModuleDetails, null=True, blank=True)
    deleted_by = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='user_deleted_by')

    is_active = models.BooleanField(default=True, null=True, blank=True)
    deleted_at = models.DateTimeField(auto_now_add=True)


class InviteDetails(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE,  null=True, blank=True)
    email = models.EmailField(max_length=100, null=True, blank=True)
    name = models.CharField(max_length=100, blank=True, null=True)
    
    is_verified = models.BooleanField(null=False, blank=True, default=False)
    is_reject = models.BooleanField(null=False, blank=True, default=False)
    is_deleted = models.BooleanField(null=False, blank=True, default=False)
    is_free_user = models.BooleanField(null=True, blank=True, default=False)
    
   
    module = models.ManyToManyField(ModuleDetails, blank=True)
    bundle = models.ManyToManyField(BundleDetails, blank=True)

class FreeSubscriptionDetails(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE,  null=True, blank=True)
   
    module = models.ManyToManyField(ModuleDetails, blank=True)
    bundle = models.ManyToManyField(BundleDetails, blank=True)
    free_subscription_start_date = models.DateField(null=True, blank=True)
    free_subscription_end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True, null=True, blank=True)
