# Python imports

# Framework imports
from flask import Blueprint, request

# Local imports
from esp32OTA.generic.services.utils import decorators, constants
from esp32OTA.UsageLogging.controllers.UsageLoggingController import UsageLoggingController

usage_logging_bp = Blueprint("usage_logging_bp", __name__)


@usage_logging_bp.route("/log", methods=["POST"])
@decorators.is_authenticated
@decorators.keys_validator(
    constants.REQUIRED_FIELDS_LIST__USAGE_LOGGING,
    request_form_data=True
)
def log_usage_view(data):
    return UsageLoggingController.log_usage(data=data)