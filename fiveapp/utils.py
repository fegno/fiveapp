from datetime import date, datetime, time
import pytz, re
from django.conf import settings
import requests
from django.utils import timezone
from io import BytesIO
from django.http import HttpResponse
from django.template.loader import get_template



def localtime(utc_dt, request):
    if not utc_dt:
        return utc_dt
    if not utc_dt.tzinfo:
        utc_dt = utc_dt.replace(tzinfo=timezone.utc)
    user_tz_offset = request.COOKIES.get("tz_offset") if request else None
    user_tz_offset = int(user_tz_offset) if user_tz_offset else 330
    user_tz = timezone.get_fixed_timezone(user_tz_offset)
    tdt = utc_dt
    time_only = isinstance(utc_dt, time)
    if time_only:
        tdt = datetime.combine(datetime.today().date(), tdt)
    time_local = timezone.localtime(tdt, timezone=user_tz)
    if time_only:
        time_local = time_local.time()
    if not settings.USE_TZ:
        return time_local.replace(tzinfo=None)
    return time_local


def local_to_utc(dt, request=None, tz=None):
    if request:
        user_tz_offset = int(request.COOKIES.get("tz_offset", "330"))
        user_tz = timezone.get_fixed_timezone(user_tz_offset)
    elif tz:
        user_tz = pytz.timezone(tz)

    tdt = dt.replace(tzinfo=user_tz)
    time_only = isinstance(tdt, time)
    if time_only:
        tdt = datetime.combine(datetime.today().date(), tdt)
    utc_dt = timezone.localtime(tdt, timezone=timezone.utc)
    if time_only:
        tdt = tdt.time()
    if not settings.USE_TZ:
        return utc_dt.replace(tzinfo=None)
    return utc_dt

def get_error(form):
    errors = dict(form.errors)
    key = tuple(errors.keys())[0]
    error = errors[key]

    if isinstance(error, (tuple, list)):
        field = key
        error = error[0]
    else:
        tkey = tuple(error.keys())[0]
        error = error[tkey][0]
        field = tkey

    field = field.replace("__all__", "").replace("non_field_errors", "")
    if field:
        message = field.replace("_", " ").title() + " : " + error
    else:
        message = error
    return message


def utc_now():
    tnow = datetime.now(pytz.utc)
    if not settings.USE_TZ:
        return tnow.replace(tzinfo=None)
    return tnow


def validate_phone_number(phone_no):
    match = re.match(r"^[-+0-9]{5,20}$", phone_no)
    return bool(match)

class PageSerializer(object):
    def __init__(
        self, page, fields=None, exclude_list=[], serialize=True, *args, **kwargs
    ):
        page_methods = (
            "end_index",
            "has_next",
            "has_other_pages",
            "has_previous",
            "start_index",
        )
        self.data = dict(
            zip(page_methods, map(lambda x: getattr(page, x)(), page_methods))
        )
        if self.data["has_next"]:
            self.data["next_page_number"] = page.next_page_number()
        if self.data["has_previous"]:
            self.data["previous_page_number"] = page.previous_page_number()
        self.data["number"] = page.number
        self.data["num_pages"] = page.paginator.num_pages
        objects = page.object_list
        if len(objects) == 0:
            self.data["items"] = []
        else:
            if not serialize:
                self.data["items"] = objects
            else:
                try:
                    if not fields:
                        model = type(objects[0])
                        fields = model._meta.get_fields(
                            include_parents=False, include_hidden=False
                        )
                        fields = [
                            f.name
                            for f in fields
                            if not f.is_relation
                            and f.concrete
                            and f.name not in exclude_list
                        ]
                    self.data["items"] = []
                    image_field_type = ImageFieldFile
                    if objects._iterable_class.__name__.endswith("ValuesIterable"):
                        get_fn = dict.get
                    else:
                        get_fn = getattr

                    for obj in objects:
                        obj_dict = {}
                        for f in fields:
                            val = get_fn(obj, f, None)
                            if type(val) == image_field_type:
                                obj_dict[f] = str(val.url) if val and val.url else None
                            elif isinstance(val, (datetime, date, time)):
                                obj_dict[f] = val.isoformat()
                            else:
                                obj_dict[f] = val
                        self.data["items"].append(obj_dict)
                except:
                    pass
