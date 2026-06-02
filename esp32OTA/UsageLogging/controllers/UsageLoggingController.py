# Python imports

# Framework imports
from flask import Response

# Local imports
from esp32OTA.generic.controllers import Controller
from esp32OTA.UsageLogging.models.UsageLogging import UsageLogging
from esp32OTA.generic.services.utils import constants, response_codes, response_utils


class UsageLoggingController(Controller):
    Model = UsageLogging  # type: ignore[assignment]

    @classmethod
    def log_usage(cls, data):
        """
        Logs usage data by mapping payload fields to Model fields.
        """
        _, _, obj = cls.db_insert_file(
            data=data, default_validation=True)
        
        return response_utils.get_response_object(
            response_code=response_codes.CODE_SUCCESS,
            response_message=response_codes.MESSAGE_SUCCESS,
            response_data=obj.display()
        )