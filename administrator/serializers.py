from rest_framework import serializers
from administrator.api import AddToCart
from payment.models import PaymentAttempt

from superadmin.models import (
    DeleteUsersLog,
    InviteDetails, 
    ModuleDetails, 
    FeatureDetails, 
    BundleDetails, 
    UserAssignedModules,
    FreeSubscriptionDetails
  
)
from user.models import UserProfile
from administrator.models import  CsvLogDetails, PurchaseDetails, SubscriptionDetails,UploadedCsvFiles
from fiveapp.custom_serializer import CustomSerializer
from user.serializers import UserSerializer

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
            "module_identifier"
        )
    def to_representation(self, obj, *args, **kwargs):
        cd = super(ModuleDetailsSerializer, self).to_representation(
            obj, *args, **kwargs
        )
        feature_benifit = tuple(FeatureDetails.objects.filter(
            is_active=True, modules=obj
        ).values("id","benifit","feature"))
        cd["feature_benifit"] = feature_benifit
        cd["free_subscribed"] = False
        if self.context.get("request"):
            if FreeSubscriptionDetails.objects.filter(
                module=obj,
                user=self.context.get("request").user
            ).exists():
                cd["free_subscribed"] = True
            if not cd["free_subscribed"]:
                if SubscriptionDetails.objects.filter(user=self.context.get("request").user, module=obj).exists():
                    cd["free_subscribed"] = True
           
        if self.context.get("from_module") and self.context.get("admin"):
            user_c = list(UserAssignedModules.objects.filter(
                is_active=True, 
                module=obj, 
                user__created_admin=self.context.get("admin")
            ).values_list("user__id", flat=True))
            cd["users_count"] = UserProfile.objects.filter(id__in=user_c).count()
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
            "module_identifier"
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
    module = ModuleDetailsSerializer(many=True)
    user = UserSerializer()
    class Meta:
        model = UserAssignedModules
        fields = ('user', 'module', 'created')

    def get_module_names(self, obj):
        # Extract and return the names of modules assigned to the user
        return [module.title for module in obj.module.all()]
    

    
class DeletedUserLogSerializers(serializers.ModelSerializer):
    user = UserSerializer()
    class Meta:
        model = DeleteUsersLog
        fields = ('user', 'module', 'deleted_by')

class UploadedCsvFilesSerializer(CustomSerializer):
    class Meta:
        model = UploadedCsvFiles
        fields = "__all__"
        extra_kwargs = {
            "created": {"format": "%d/%m/%Y %I:%M %p"},
            "updated": {"format": "%d/%m/%Y %I:%M %p"},
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
            "created": {"format": "%d/%m/%Y %I:%M %p"},
            "updated": {"format": "%d/%m/%Y %I:%M %p"},
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
    user = UserSerializer()
    module = ModuleDetailsSerializer(many=True,)

    class Meta:
        model = SubscriptionDetails
        fields = ( "user","module", "bundle")



class ModuleSToUserserializer(serializers.Serializer):
    # user_id = serializers.IntegerField()
    module_ids = serializers.ListField(child=serializers.IntegerField(), default=[])


class CartSerializer(serializers.ModelSerializer):
    added_by = UserSerializer()
    class Meta:
        model = AddToCart
        fields = ('added_by', 'count', 'amount')



class PurchaseHistorySerializer(serializers.ModelSerializer):
    user = UserSerializer()
    module = ModuleDetailsSerializer(many=True)
    bundle = BundleDetailsSerializer(many=True)
    class Meta:
        model = PurchaseDetails
        fields = ('id', 'user', 'module', 'bundle', 'total_price', 'subscription_start_date', 'subscription_end_date', 'subscription_type','received_amounts', 'payment_dates','parchase_user_type', 'status')

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        
        # representation['user'] = {
        #     'id':instance.user.id,
        #     'first_name': instance.user.first_name,
        #     'email': instance.user.email
        # }
        representation['module'] = [{'id': module.id, 'title': module.title, 'description':module.description} for module in instance.module.all()]
        representation['bundle'] = [{'id':bundle.id, 'title':bundle.title} for bundle in instance.bundle.all()]
        return representation
    

class UserPurchaseHistorySerializer(serializers.ModelSerializer):
    user = UserSerializer()
    class Meta:
        model = PurchaseDetails
        fields = ('user', 'total_price', 'subscription_start_date', 'subscription_end_date', 'subscription_type', 'status', 'user_count')

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['user'] = instance.user.id
        return representation


class SubscriptionPaymentAttemptsSerializer(serializers.ModelSerializer):
    parchase = PurchaseHistorySerializer()
    class Meta:
        model = PaymentAttempt
        fields = ('parchase', 'payment_intent_id', 'amount', 'total_charge', 'client_secret', 'last_attempt_date')


class UserPurchaseHistorySerializers(serializers.ModelSerializer):
    user = UserSerializer()
    class Meta:
        model = PurchaseDetails
        fields = (
            'user', 'bill', 
            'card', 'subscription_start_date', 
            'subscription_end_date', 'is_subscribed', 
            'subscription_type', 'received_amounts', 
            'payment_dates', 'parchase_user_type',
            'user_count', 'status'
            )


class UserPaymentAttemptsSerializer(serializers.ModelSerializer):
    parchase = UserPurchaseHistorySerializers()
    class Meta:
        model = PaymentAttempt
        fields = ('parchase', 'payment_intent_id', 'amount', 'total_charge', 'client_secret', 'last_attempt_date')


class InvitedUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = InviteDetails
        fields = ('name', 'email')
