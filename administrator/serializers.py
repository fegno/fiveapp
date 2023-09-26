from rest_framework import serializers

from superadmin.models import (
    DeleteUsersLog, 
    ModuleDetails, 
    FeatureDetails, 
    BundleDetails, 
    UserAssignedModules,
  
)
from administrator.models import  CsvLogDetails, SubscriptionDetails,UploadedCsvFiles
from fiveapp.custom_serializer import CustomSerializer

class ModuleDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model= ModuleDetails
        fields = (
            "id",
            "department",
            "title",
            "description",
            "bundle_name",
            "csv_file",
            "position",
            "weekly_price",
            "monthly_price",
            "yearly_price",
            "is_submodule",
        )
    def to_representation(self, obj, *args, **kwargs):
        cd = super(ModuleDetailsSerializer, self).to_representation(
            obj, *args, **kwargs
        )
        feature_benifit = tuple(FeatureDetails.objects.filter(
            is_active=True, modules=obj
        ).values("id","benifit","feature"))
        cd["feature_benifit"] = feature_benifit
        if self.context.get("from_module"):
            cd["users_count"] = UserAssignedModules.objects.filter(
                is_active=True, module=obj
            ).count()
        return cd


class BundleDetailsSerializer(serializers.ModelSerializer):
    modules = ModuleDetailsSerializer(many=True)
    class Meta:
        model= BundleDetails
        fields = (
            "id",
            "weekly_price",
            "monthly_price",
            "yearly_price",
            "title",
            "icon",
            "modules"
        )
    def to_representation(self, obj, *args, **kwargs):
        cd = super(BundleDetailsSerializer, self).to_representation(
            obj, *args, **kwargs
        )
        return cd

class ModuleLiteSerializer(serializers.ModelSerializer):
    class Meta:
        model= ModuleDetails
        fields = (
            "id",
            "department",
            "title",
            "description",
            "bundle_name",
            "csv_file",
            "position",
            "weekly_price",
            "monthly_price",
            "yearly_price",
        )
    def to_representation(self, obj, *args, **kwargs):
        cd = super(ModuleLiteSerializer, self).to_representation(
            obj, *args, **kwargs
        )
        feature_benifit = tuple(FeatureDetails.objects.filter(
            is_active=True, modules=obj
        ).values("id","benifit","feature"))
        cd["feature_benifit"] = feature_benifit
        
        sub_modules = ModuleDetails.objects.filter(modules=obj)
        cd["sub_modules"] = ModuleDetailsSerializer(sub_modules, many=True).data
        return cd

class BundleDetailsLiteSerializer(serializers.ModelSerializer):
    class Meta:
        model= BundleDetails
        fields = (
            "id",
            "weekly_price",
            "monthly_price",
            "yearly_price",
            "title",
            "icon",
            "modules"
        )
    def to_representation(self, obj, *args, **kwargs):
        cd = super(BundleDetailsLiteSerializer, self).to_representation(
            obj, *args, **kwargs
        )
        cd["modules"] = ModuleLiteSerializer(
            obj.modules.all().filter(is_submodule=False),many=True).data
        return cd
    

class UserAssignedModuleSerializers(serializers.ModelSerializer):
    class Meta:
        model = UserAssignedModules
        fields = ('user', 'module', 'created')

    
class DeletedUserLogSerializers(serializers.ModelSerializer):
    class Meta:
        model = DeleteUsersLog
        fields = ('user', 'module', 'deleted_by')

class UploadedCsvFilesSerializer(CustomSerializer):
    class Meta:
        model = UploadedCsvFiles
        fields = "__all__"
        extra_kwargs = {
            "created": {"format": "%d/%m/%Y %H:%M"},
            "updated": {"format": "%d/%m/%Y %H:%M"},
        }
    def to_representation(self, obj, *args, **kwargs):
        cd = super(UploadedCsvFilesSerializer, self).to_representation(
            obj, *args, **kwargs
        )
        cd["uploaded_by_name"] = obj.uploaded_by.first_name
        return cd

class CsvSerializers(serializers.ModelSerializer):
    class Meta:
        model = CsvLogDetails
        fields = "__all__"
        extra_kwargs = {
            "created": {"format": "%d/%m/%Y %H:%M"},
            "updated": {"format": "%d/%m/%Y %H:%M"},
        }
    def to_representation(self, obj, *args, **kwargs):
        cd = super(CsvSerializers, self).to_representation(
            obj, *args, **kwargs
        )
        cd["uploaded_Details"] =UploadedCsvFilesSerializer(
            obj.uploaded_file, context={'request':self.context.get("request")}).data
        return cd
    

class UserInviteSerializer(serializers.Serializer):
    email = serializers.EmailField()
    first_name = serializers.CharField()
    selected_modules = serializers.ListField(child=serializers.IntegerField(), required=False)


class SubscriptionModuleSerilzer(serializers.Serializer):
    model = SubscriptionDetails
    fields = ("user", "module", "bundle")