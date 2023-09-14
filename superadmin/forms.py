from django.forms import ModelForm
from superadmin.models import *


class ModuleForm(ModelForm):
    class Meta:
        model = ModuleDetails
        fields = [
            "title",
            "description",
            "bundle_name",
            "csv_file",
            "position",
            "weekly_price",
            "monthly_price",
            "yearly_price",
            "modules",
            "is_submodule"
        ]

