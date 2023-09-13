from django.template.defaulttags import register
import json
import re
from datetime import datetime, timedelta
from fiveapp.utils import utc_now
from django.utils.safestring import mark_safe


@register.filter
def dateformat(value):
    if value:
        value = value + timedelta(hours=24)
        edit = True if value > utc_now() else False
        return edit


@register.filter(name="json", needs_autoescape=False)
def tojson(value):
    return mark_safe(json.dumps(value))


@register.filter(name="page_links")
def pagination_links(page):
    return_dict = {"prev_three": (), "next_three": ()}
    page_methods = (
        "end_index",
        "has_next",
        "has_other_pages",
        "has_previous",
        "start_index",
    )

    data = dict(zip(page_methods, map(lambda x: getattr(page, x)(), page_methods)))
    if data["has_previous"]:
        return_dict["prev_three"] = range(max(page.number - 3, 1), page.number, 1)
        return_dict["show_first"] = return_dict["prev_three"][0] != 1
    if data["has_next"]:
        return_dict["next_three"] = range(
            page.number + 1, min(page.paginator.num_pages + 1, page.number + 4), 1
        )
        return_dict["show_last"] = (
            return_dict["next_three"][-1] != page.paginator.num_pages
        )
    return return_dict
