# Python imports

# Framework imports
from flask import Blueprint, request

# Local imports
from esp32OTA.generic.services.utils import decorators, constants, response_codes, response_utils
from esp32OTA.PingLogging.controllers.PingLoggingController import PingLoggingController

ping_logging_bp = Blueprint("ping_logging_bp", __name__)


@ping_logging_bp.route("/log", methods=["POST"])
@decorators.is_authenticated
@decorators.keys_validator(
    constants.REQUIRED_FIELDS_LIST__PING_LOGGING,
    request_form_data=True
)
def log_ping_view(data):
    obj = PingLoggingController.log_ping(data=data)
    return response_utils.get_response_object(
        response_code=response_codes.CODE_SUCCESS,
        response_message=response_codes.MESSAGE_SUCCESS,
        response_data=obj.display() if obj else {}
    )


@ping_logging_bp.route("/read", methods=["GET"])
def read_ping_view():
    return PingLoggingController.read_controller()
