# Python imports
import os
import re
from datetime import datetime
# Framework imports
from flask import Blueprint, redirect, url_for, redirect, render_template, request

# Local imports
from esp32OTA.generic.services.utils import constants, decorators, common_utils, response_codes, response_utils
from esp32OTA.Logging.controllers.LoggingController import LoggingController
from esp32OTA.config import config

logging_bp = Blueprint("logging_bp", __name__)


@logging_bp.route("/log", methods=["POST"])
@decorators.is_authenticated
@decorators.keys_validator(
    ["payload"],
    request_form_data=True
)
def log_view(data):
    return LoggingController.log_controller(data=data)

