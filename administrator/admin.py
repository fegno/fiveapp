from django.contrib import admin
from administrator.models import AddToCart, PurchaseDetails, SubscriptionDetails, CsvLogDetails, UploadedCsvFiles

admin.site.register(SubscriptionDetails)
admin.site.register(PurchaseDetails)
admin.site.register(CsvLogDetails)
admin.site.register(UploadedCsvFiles)
admin.site.register(AddToCart)
