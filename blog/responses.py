from rest_framework import status as http_status
from rest_framework.response import Response


class APIResponse(Response):
    """One response shape for the entire API."""

    def __init__(self, data=None, message='', status=http_status.HTTP_200_OK, errors=None):
        if status == http_status.HTTP_204_NO_CONTENT:
            super().__init__(status=status)
            return

        payload = {
            'success': status < 400,
            'message': message or default_message(status),
        }

        if status < 400:
            payload['data'] = data if data is not None else {}
        else:
            payload['errors'] = normalize_errors(errors if errors is not None else data)

        super().__init__(data=payload, status=status)


def default_message(status):
    return {
        200: 'OK.',
        201: 'Created.',
        400: 'Please check the information you entered.',
        401: 'Please sign in to continue.',
        403: "You don't have permission to do that.",
        404: 'Not found.',
        409: 'That conflicts with the current state.',
    }.get(status, 'Something went wrong.')


def normalize_errors(raw):
    """Turn anything DRF throws at us into {field: [message, ...]}."""
    if raw is None:
        return {'non_field_errors': ['Something went wrong.']}
    if isinstance(raw, str):
        return {'non_field_errors': [raw]}
    if isinstance(raw, list):
        return {'non_field_errors': [str(item) for item in raw]}
    if isinstance(raw, dict):
        return {
            key: [str(v) for v in (value if isinstance(value, list) else [value])]
            for key, value in raw.items()
        }
    return {'non_field_errors': [str(raw)]}
