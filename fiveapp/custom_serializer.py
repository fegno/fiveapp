from rest_framework import serializers
from fiveapp.utils import validate_phone_number, localtime, local_to_utc
from datetime import datetime


class CustomSerializer(serializers.ModelSerializer):
    time_fields_to_convert = []

    def __init__(self, *args, **kwargs):
        localize = kwargs.pop("localize", False)
        request = kwargs.pop("request", None)
        self.localize_data = localize
        if self.localize_data:
            self.request = request
        super(CustomSerializer, self).__init__(*args, **kwargs)

    def to_internal_value(self, dt, *args, **kwargs):
        tdt = super(CustomSerializer, self).to_internal_value(dt)
        tdt._mutable = True
        if self.localize_data:
            for name in self.time_fields_to_convert:
                val = tdt.get(name)
                if not val:
                    continue
                tdt[name] = local_to_utc(val, self.request)
        tdt._mutable = False
        return tdt

    def validate(self, data):
        t_data = super(CustomSerializer, self).validate(data)
        phone_no_fields = ("mobile_no",)
        for field in phone_no_fields:
            val = t_data.get(field)
            if val and not validate_phone_number(val):
                raise serializers.ValidationError({field: "Invalid mobile number"})
        return t_data

    def to_representation(self, obj):
        data = super(CustomSerializer, self).to_representation(obj)
        getter = dict.get if isinstance(obj, dict) else getattr
        if self.localize_data:
            default_format = "%d/%m/%Y %I:%M:%S %p"
            for name, field in self.fields.items():
                if isinstance(
                    field, (serializers.DateTimeField, serializers.TimeField)
                ):
                    val = getter(obj, name, None)
                    if not val:
                        continue
                    dtformat = getattr(field, "format", None) or default_format
                    local_inst = localtime(val, self.request)
                    data[name] = local_inst.strftime(dtformat)
        return data
