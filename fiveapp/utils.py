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

