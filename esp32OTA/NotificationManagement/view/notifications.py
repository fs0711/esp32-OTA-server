# Python imports
import os
import re
from datetime import datetime
# Framework imports
from flask import Blueprint, redirect, url_for, redirect, render_template, request

# Local imports
from esp32OTA.generic.services.utils import constants, decorators, common_utils
from esp32OTA.NotificationManagement.controller.NotificationsController import NotificationController
from esp32OTA.config import config

# device_bp = Blueprint("device_bp", __name__)


# @device_bp.route("/create", methods=["POST"])
# @decorators.is_authenticated
# @decorators.keys_validator(
#     constants.REQUIRED_FIELDS_LIST__DEVICE,
#     constants.OPTIONAL_FIELDS_LIST__DEVICE,
#     request_form_data=True
# )
# def create_view(data):
#     return DeviceController.create_controller(data=data)

