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


@firmware_bp.route("/read", methods=["GET", "POST"])
@decorators.is_authenticated
@decorators.keys_validator()
def read_view(data):
    if request.method == "POST":
        data = request.form
    return FirmwareController.read_controller(data=data)


@firmware_bp.route("/update", methods=["PUT"])
@decorators.is_authenticated
# @decorators.roles_allowed([constants.ROLE_ID_ADMIN])
@decorators.keys_validator()
def update_view(data):
    return FirmwareController.update_controller(data=data)

@firmware_bp.route("/search", methods=["POST", "GET"])
@decorators.is_authenticated
@decorators.keys_validator()
def search_view(data):
    return FirmwareController.search_controller(data=data)
