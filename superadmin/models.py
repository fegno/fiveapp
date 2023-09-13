from django.db import models

Type_Choice = (
    ("Team Indicator", "Team Indicator"),
    ("Team Workforce Plan Corporate", "Team Workforce Plan Corporate"),
    ("Team Cost HR Costing and Accounting department", "Team Cost HR Costing and Accounting department"),
    ("Payroll Analytics - Business Services", "Payroll Analytics - Business Services"),
    ("Gender analytics - Finance and HR department", "Gender analytics - Finance and HR department"),
    ("UTILITY METER - SUPPLY CHAIN","UTILITY METER - SUPPLY CHAIN"),
    ("METRICS METER / SALE CENTRE","METRICS METER / SALE CENTRE"),
    ("Warehouse MAP Retail","Warehouse MAP Retail"),
    ("Logistic Controller","Logistic Controller"),
    ("ODOMETERS: BACK OFFICE","ODOMETERS: BACK OFFICE")
)


class ModuleDetails(models.Model):
    title = models.CharField(null=True, blank=True, max_length=1000, choices=Type_Choice,)
    description = models.TextField(null=True, blank=True)
    bundle_name = models.TextField(null=True, blank=True)
    csv_file = models.FileField(null=True, blank=True)
    position = models.IntegerField(default=0)

    is_active = models.BooleanField(null=False, blank=True, default=True)
    created = models.DateTimeField(auto_now_add=True)
