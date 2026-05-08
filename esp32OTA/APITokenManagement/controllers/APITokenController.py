# Python imports

# Local imports
from esp32OTA.generic.controllers import Controller
from esp32OTA.APITokenManagement.models.APIToken import APIToken
from esp32OTA.generic.services.utils import common_utils, constants, response_utils, response_codes


class APITokenController(Controller):
    Model = APIToken

    @classmethod
    def create_controller(cls, data):
        """
        Create a new API token with default 1 year expiry.
        Required: service_name
        """
        data[constants.TOKEN__ACCESS_TOKEN] = common_utils.generate_uuid4()
        # Default expiry 1 year
        data[constants.TOKEN__EXPIRY_TIME] = common_utils.get_time(days=365)
        # Set active by default
        data[constants.TOKEN__IS_ACTIVE] = True
        # Initialize last_used to 0
        data['last_used'] = 0
        
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
    def read_controller(cls, data):
        """
        Read API tokens with optional filtering.
        """
        read_filter = data if data else {}
        
        tokens = cls.db_read_records(read_filter=read_filter, deleted_records=False)
        return response_utils.get_response_object(
            response_code=response_codes.CODE_SUCCESS,
            response_message=response_codes.MESSAGE_SUCCESS,
            response_data=[token.display() for token in tokens]
        )

    @classmethod
    def validate_token(cls, token_string):
        """
        Validate API token and auto-extend expiry.
        Returns token object if valid, None otherwise.
        """
        read_filter = {constants.TOKEN__ACCESS_TOKEN: token_string}
        token_obj = cls.db_read_single_record(read_filter)
        
        if not token_obj:
            return None
        
        # Check if token is active
        if not token_obj.is_active:
            return None
        
        # Check if token is expired
        current_time = common_utils.get_time()
        if current_time > token_obj.expiry_time:
            return None
        
        # Auto-extend expiry by 1 year
        token_obj.expiry_time = common_utils.get_time(days=365)
        token_obj.last_used = current_time
        token_obj.save()
        
        return token_obj

    @classmethod
    def suspend_controller(cls, data):
        """
        Suspend an API token.
        Required: access_token OR id
        """
        # Determine filter based on provided field
        read_filter = {}
        if constants.TOKEN__ACCESS_TOKEN in data:
            read_filter[constants.TOKEN__ACCESS_TOKEN] = data[constants.TOKEN__ACCESS_TOKEN]
        elif constants.ID in data:
            read_filter[constants.ID] = data[constants.ID]
        else:
            return response_utils.get_response_object(
                response_code=response_codes.CODE_VALIDATION_FAILED,
                response_message="Token access_token or id is required",
                response_data=[]
            )
        
        token_obj = cls.db_read_single_record(read_filter)
        
        if not token_obj:
            return response_utils.get_response_object(
                response_code=response_codes.CODE_RECORD_NOT_FOUND,
                response_message="API Token not found",
                response_data=[]
            )
        
        # Deactivate the token
        token_obj.update(set__is_active=False)
        token_obj.save()
        
        return response_utils.get_response_object(
            response_code=response_codes.CODE_SUCCESS,
            response_message="API Token suspended successfully",
            response_data=token_obj.display()
        )

    @classmethod
    def delete_controller(cls, data):
        """
        Delete an API token.
        Required: access_token OR id
        """
        # Determine filter based on provided field
        read_filter = {}
        if constants.TOKEN__ACCESS_TOKEN in data:
            read_filter[constants.TOKEN__ACCESS_TOKEN] = data[constants.TOKEN__ACCESS_TOKEN]
        elif constants.ID in data:
            read_filter[constants.ID] = data[constants.ID]
        else:
            return response_utils.get_response_object(
                response_code=response_codes.CODE_VALIDATION_FAILED,
                response_message="Token access_token or id is required",
                response_data=[]
            )
        
        token_obj = cls.db_read_single_record(read_filter)
        
        if not token_obj:
            return response_utils.get_response_object(
                response_code=response_codes.CODE_RECORD_NOT_FOUND,
                response_message="API Token not found",
                response_data=[]
            )
        
        token_obj.delete()
        
        return response_utils.get_response_object(
            response_code=response_codes.CODE_SUCCESS,
            response_message="API Token deleted successfully",
            response_data=[]
        )
