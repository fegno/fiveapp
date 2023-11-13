from django.contrib import admin
from .models import *

admin.site.register(ModuleDetails)
admin.site.register(FeatureDetails)
admin.site.register(BundleDetails)
admin.site.register(UserAssignedModules)
admin.site.register(DeleteUsersLog)
admin.site.register(InviteDetails)

