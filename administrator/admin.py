from django.contrib import admin
from administrator.models import *

admin.site.register(SubscriptionDetails)
admin.site.register(PurchaseDetails)
admin.site.register(CsvLogDetails)
admin.site.register(UploadedCsvFiles)
admin.site.register(AddToCart)
admin.site.register(CustomRequest)
admin.site.register(DepartmentWeightage)


