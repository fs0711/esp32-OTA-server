# Python imports

# Local imports
from esp32OTA.generic.services.utils import (
    common_utils, response_utils, response_codes, constants)
from esp32OTA.config import config
# Framework imports
from functools import wraps


def logging(view_function):

    @wraps(view_function)
    def wrapper(*args, **kwargs):
        if config.FUNCTION_LOGGING:
            try:
                response = view_function(*args, **kwargs)
                return response

            except Exception as e:
                print(str(e))
                response = response_utils.get_response_object(
                    response_code=response_codes.CODE_HTTP_452,
                    response_message=response_codes.MESSAGE_GENERAL_ERROR)
                return response
        else:
            response = view_function(*args, **kwargs)
            return response

    return wrapper


def keys_validator(required_fields=[], optional_fields=[],
                   request_form_data=True):

    def decorator(view_function):

        @wraps(view_function)
        def wrapper(*args, **kwargs):
            if request_form_data:
                data = common_utils.posted()
            else:
                data = common_utils.posted_files()
                
            if not required_fields and not optional_fields:
                return view_function({}, *args, **kwargs)

            validated_keys = {
                key: data.get(key) for key in required_fields
                if data.get(key) not in [None, "", [], {}]}

            if set(validated_keys) != set(required_fields):
                message = "Missing parameters keys: {}".format(
                    ' '.join(set(required_fields) - set(validated_keys)))
                response = response_utils.get_response_object(
                    response_code=response_codes.CODE_MISSING_PARAMETERS,
                    response_message=message)
                return response
            available_fields = []
            available_fields.extend(required_fields)
            available_fields.extend(optional_fields)
            new_data = {key: data.get(key) for key in available_fields if data.get(
                key) not in [None, "", [], {}]}
            return view_function(new_data, *args, **kwargs)

        return wrapper

    return decorator


def is_authenticated(view_function):

    @wraps(view_function)
    def decorator(*args, **kwargs):
        token_obj, _ = common_utils.get_token()
        if not token_obj:
            return response_utils.get_response_object(
                response_code=response_codes.CODE_UNAUTHENTICATED_ACCESS,
                response_message=response_codes.MESSAGE_UNAUTHENTICATED_ACCESS)
        current_timestamp = common_utils.get_time()
        if not(current_timestamp > token_obj[constants.TOKEN__EXPIRY_TIME]):
            if token_obj[constants.TOKEN__PLATFORM] == constants.PLATFORM_WEB:
                token_obj[constants.TOKEN__EXPIRY_TIME] = common_utils.get_time(offset=config.TOKEN_EXPIRY_TIME_WEB)
            if token_obj[constants.TOKEN__PLATFORM] == constants.PLATFORM_MOBILE:
                token_obj[constants.TOKEN__EXPIRY_TIME] = common_utils.get_time(days=config.TOKEN_EXPIRY_TIME_MOBILE)
            if token_obj[constants.TOKEN__PLATFORM] == constants.PLATFORM_DEVICE:
                token_obj[constants.TOKEN__EXPIRY_TIME] = common_utils.get_time(days=config.TOKEN_EXPIRY_TIME_DEVICE)
            token_obj[constants.UPDATED_ON] = current_timestamp
            token_obj.save()
        else:
            token_obj.is_expired = True
            token_obj.save()
            return response_utils.get_response_object(
                response_code=response_codes.CODE_TOKEN_EXPIRED,
                response_message=response_codes.MESSAGE_TOKEN_EXPIRED)

        return view_function(*args, **kwargs)

    return decorator


def roles_allowed(role_ids):

    def wrapper(view_function):

        @wraps(view_function)
        def wrap(*args, **kwargs):

            user = common_utils.current_user()
            if user[constants.USER__ROLE][constants.USER__ROLE__ROLE_ID] not in role_ids:
                response = response_utils.get_response_object(
                        response_code=response_codes.CODE_UNAUTHORIZED_ACCESS,
                        response_message=response_codes.MESSAGE_UNAUTHORIZED_ACCESS)
                return response

            return view_function(*args, **kwargs)

        return wrap

    return wrapper


def blocked(view_function):

    @wraps(view_function)
    def wrapper(*args, **kwargs):

        response = response_utils.get_response_object(
            response_code=response_codes.CODE_DEPRECATED_API,
            response_message=response_codes.MESSAGE_DEPRECATED_API)
        return response

    return wrapper
