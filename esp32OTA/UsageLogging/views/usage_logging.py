# Python imports

# Framework imports
from flask import Blueprint, request

# Local imports
from esp32OTA.generic.services.utils import decorators, constants, response_codes, response_utils
from esp32OTA.UsageLogging.controllers.UsageLoggingController import UsageLoggingController

usage_logging_bp = Blueprint("usage_logging_bp", __name__)


@usage_logging_bp.route("/log", methods=["POST"])
@decorators.is_authenticated
@decorators.keys_validator(
    constants.REQUIRED_FIELDS_LIST__USAGE_LOGGING,
    request_form_data=True
)
def log_usage_view(data):
    obj = UsageLoggingController.log_usage(data=data)
    return response_utils.get_response_object(
        response_code=response_codes.CODE_SUCCESS,
        response_message=response_codes.MESSAGE_SUCCESS,
        response_data=obj.display() if obj else {}
    )


@usage_logging_bp.route("/read", methods=["GET"])
def read_usage_view():
    return UsageLoggingController.read_controller()
