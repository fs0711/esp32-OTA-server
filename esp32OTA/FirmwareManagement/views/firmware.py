# Python imports
import os
import re
from datetime import datetime
# Framework imports
from flask import Blueprint, redirect, url_for, redirect, render_template, request

# Local imports
from esp32OTA.generic.services.utils import constants, decorators, common_utils
from esp32OTA.FirmwareManagement.controllers.FirmwareController import FirmwareController
from esp32OTA.config import config

firmware_bp = Blueprint("firmware_bp", __name__)


@firmware_bp.route("/upload", methods=["POST"])
@decorators.is_authenticated
@decorators.keys_validator(
    constants.REQUIRED_FIELDS_LIST__FIRMWARE,
    constants.OPTIONAL_FIELDS_LIST__FIRMWARE,
    request_form_data=False
)
def upload_view(data):
    return FirmwareController.upload_controller(data=data)


@firmware_bp.route("/read", methods=["GET"])
@decorators.is_authenticated
@decorators.keys_validator()
def read_view(data):
    return FirmwareController.read_controller(data=data)


@firmware_bp.route("/assign", methods=["POST"])
@decorators.is_authenticated
@decorators.keys_validator(
    [constants.ID, constants.DEVICE_TYPE__ID],
    [],
    request_form_data=True
)
def assign_to_device_type_view(data):
    return FirmwareController.assign_firmware_to_device_type(data=data)
