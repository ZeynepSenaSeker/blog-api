from rest_framework.views import exception_handler
from .responses import APIResponse


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return None  # not a DRF error — let Django handle it
    return APIResponse(errors=response.data, status=response.status_code)
