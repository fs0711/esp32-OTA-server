# Python imports
import os
import re
from datetime import datetime
# Framework imports
from flask import Blueprint, redirect, url_for, redirect, render_template, request

# Local imports
from esp32OTA.generic.services.utils import constants, decorators, common_utils, response_codes, response_utils
from esp32OTA.GatewayLogging.controllers.GatewayLoggingController import GatewayLoggingController
from esp32OTA.config import config

gateway_logging_bp = Blueprint("gateway_logging_bp", __name__)


@gateway_logging_bp.route("/log", methods=["POST"])
@decorators.is_authenticated
@decorators.keys_validator(
    ["payload"],
    request_form_data=True
)
def log_view(data):
    return GatewayLoggingController.log_controller(data=data)

