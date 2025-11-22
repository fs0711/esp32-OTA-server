# Python imports
import os
import re
from datetime import datetime
# Framework imports
from flask import Blueprint, redirect, url_for, redirect, render_template, request

# Local imports
from esp32OTA.generic.services.utils import constants, decorators, common_utils
from esp32OTA.DeviceManagement.controllers.DeviceController import DeviceController
from esp32OTA.config import config

device_bp = Blueprint("device_bp", __name__)


@device_bp.route("/create", methods=["POST"])
@decorators.is_authenticated
@decorators.keys_validator(
    constants.REQUIRED_FIELDS_LIST__DEVICE,
    constants.OPTIONAL_FIELDS_LIST__DEVICE,
    request_form_data=True
)
def create_view(data):
    return DeviceController.create_controller(data=data)


@device_bp.route("/read", methods=["GET", "POST"])
@decorators.is_authenticated
@decorators.keys_validator()
def read_view(data):
    if request.method == "POST":
        data = request.form
    return DeviceController.read_controller(data=data)


@device_bp.route("/getclients", methods=["GET"])
@decorators.is_authenticated
# @decorators.keys_validator()
def get_view():
    return DeviceController.get_clients()


@device_bp.route("/update", methods=["PUT"])
@decorators.is_authenticated
# @decorators.roles_allowed([constants.ROLE_ID_ADMIN])
@decorators.keys_validator()
def update_view(data):
    return DeviceController.update_controller(data=data)

@device_bp.route("/config", methods=["POST", "GET"])
@decorators.is_authenticated
@decorators.keys_validator()
def search_view(data):
    return DeviceController.config_controller(data=data)

# @device_bp.route("/search", methods=["POST", "GET"])
# @decorators.is_authenticated
# @decorators.keys_validator()
# def search_view(data):
#     return DeviceController.search_controller(data=data)
