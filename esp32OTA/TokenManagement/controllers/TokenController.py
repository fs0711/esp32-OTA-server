# Python imports

# Local imports
from esp32OTA.generic.controllers import Controller
from esp32OTA.TokenManagement.models.Token import Token
from esp32OTA.generic.services.utils import common_utils, constants, response_utils, response_codes


class TokenController(Controller):
    Model = Token

    @classmethod
    def create_controller(cls, data):
        data[constants.TOKEN__ACCESS_TOKEN] = common_utils.generate_uuid4()
        # Hardcoded expiry 1 year
        data[constants.TOKEN__EXPIRY_TIME] = common_utils.get_time(days=365)
        # Set active by default
        data[constants.TOKEN__IS_ACTIVE] = True
        
        is_valid, errors, obj = cls.db_insert_record(data)
        if is_valid:
            return response_utils.get_response_object(
                response_code=response_codes.CODE_SUCCESS,
                response_message=response_codes.MESSAGE_SUCCESS,
                response_data=obj.display()
            )
        return response_utils.get_response_object(
            response_code=response_codes.CODE_VALIDATION_FAILED,
            response_message=response_codes.MESSAGE_VALIDATION_FAILED,
            response_data=errors
        )

    @classmethod
    def validate_token(cls, token_string):
        token_obj = cls.db_read_single_record({
            constants.TOKEN__ACCESS_TOKEN: token_string,
            constants.TOKEN__IS_ACTIVE: True
        })
        
        if token_obj:
            if token_obj.expiry_time < common_utils.get_time():
                token_obj.update(set__is_active=False)
                return None
            return token_obj
        return None

