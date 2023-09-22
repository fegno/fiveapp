from django.contrib import admin
from administrator.models import PurchaseDetails, SubscriptionDetails, CsvLogDetails, UploadedCsvFiles

admin.site.register(SubscriptionDetails)
admin.site.register(PurchaseDetails)
admin.site.register(CsvLogDetails)
admin.site.register(UploadedCsvFiles)
