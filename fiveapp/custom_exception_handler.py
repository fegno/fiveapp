from rest_framework.views import exception_handler


def handler(exc, context):
    response = exception_handler(exc, context)
    if response is not None:
        response.data["status_code"] = response.status_code
        response.data["detail"] = str(exc)
    return response
