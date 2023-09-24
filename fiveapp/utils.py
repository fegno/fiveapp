from datetime import date, datetime, time
import pytz
from django.conf import settings
import requests
from io import BytesIO
from django.http import HttpResponse
from django.template.loader import get_template


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
