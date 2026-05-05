# Python imports
import os
import re
from datetime import datetime
# Framework imports
from flask import Blueprint, redirect, url_for, redirect, render_template, request

# Local imports
from esp32OTA.generic.services.utils import constants, decorators, common_utils, response_codes, response_utils
from esp32OTA.FirmwareManagement.controllers.FirmwareController import FirmwareController
from esp32OTA.FirmwareManagement.models.Firmware import Firmware
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


@firmware_bp.route("/update", methods=["PUT"])
@decorators.is_authenticated
@decorators.keys_validator(
    [constants.ID],
    constants.UPDATE_FIELDS_LIST__FIRMWARE,
    request_form_data=True
)
def update_view(data):
    return FirmwareController.update_controller(data=data)


@firmware_bp.route("/suspend", methods=["DELETE"])
@decorators.is_authenticated
@decorators.keys_validator(
    [constants.ID],
    [],
    request_form_data=True
)
def suspend_view(data):
    return FirmwareController.suspend_controller(data=data)


@firmware_bp.route("/assign", methods=["POST"])
@decorators.is_authenticated
@decorators.keys_validator(
    [constants.ID, constants.DEVICE_TYPE__ID],
    [],
    request_form_data=True
)
def assign_to_device_type_view(data):
    return FirmwareController.assign_firmware_to_device_type(data=data)


@firmware_bp.route("/download", methods=["GET"])
#@decorators.is_authenticated
@decorators.keys_validator(
    [constants.ID],
    ["chunk_size"],
    request_form_data=True
)
def download_firmware_view(data):
    return FirmwareController.download_firmware(data=data)

