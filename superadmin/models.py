from django.db import models

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
    ("Warehouse MAP Retail","Warehouse MAP Retail"),
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
    report = models.TextField(null=True, blank=True)

    is_active = models.BooleanField(null=False, blank=True, default=True)
    created = models.DateTimeField(auto_now_add=True)
