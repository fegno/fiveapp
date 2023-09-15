from rest_framework import serializers

from superadmin.models import ModuleDetails


class ModuleDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model= ModuleDetails
        fields = '__all__'
