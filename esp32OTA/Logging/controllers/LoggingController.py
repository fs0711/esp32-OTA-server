# Python imports
import re
from math import nan, isnan
# Framework imports
from flask import Response, stream_with_context

# Local imports
from ast import Constant
from esp32OTA.generic.controllers import Controller
from esp32OTA.Logging.models.Logging import Logging
from esp32OTA.generic.services.utils import constants, response_codes, response_utils, common_utils, pipeline


class LoggingController(Controller):
    Model = Logging # type: ignore[assignment]

    @classmethod
    def log_controller(cls, data):
        _, _, obj = cls.db_insert_file(
            data=data, default_validation=False)
        return response_utils.get_response_object(
            response_code=response_codes.CODE_SUCCESS,
            response_message=response_codes.MESSAGE_SUCCESS,
            response_data=obj.display()
        )

