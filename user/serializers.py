from rest_framework import serializers
from user.models import UserProfile

class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = (
            "first_name",
            "mobile_no",
            "last_name",
            "email",
            "company_name",
            "industrial_size",
            "employee_position",
        )
