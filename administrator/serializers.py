from rest_framework import serializers

from superadmin.models import ModuleDetails, FeatureDetails, BundleDetails


class ModuleDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model= ModuleDetails
        fields = (
            "department",
            "title",
            "description",
            "bundle_name",
            "csv_file",
            "position",
            "weekly_price",
            "monthly_price",
            "yearly_price",
            "is_submodule"
        )
    def to_representation(self, obj, *args, **kwargs):
        cd = super(ModuleDetailsSerializer, self).to_representation(
            obj, *args, **kwargs
        )
        feature_benifit = tuple(FeatureDetails.objects.filter(
            is_active=True, modules=obj
        ).values("id","benifit","feature"))
        cd["feature_benifit"] = feature_benifit
        return cd


class BundleDetailsSerializer(serializers.ModelSerializer):
    modules = ModuleDetailsSerializer(many=True)
    class Meta:
        model= BundleDetails
        fields = (
            "weekly_price",
            "monthly_price",
            "yearly_price",
            "title",
            "icon"
        )
    def to_representation(self, obj, *args, **kwargs):
        cd = super(BundleDetailsSerializer, self).to_representation(
            obj, *args, **kwargs
        )
        return cd