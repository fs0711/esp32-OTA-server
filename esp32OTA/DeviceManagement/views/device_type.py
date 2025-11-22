# Python imports

# Framework imports
from flask import Blueprint, request

# Local imports
from esp32OTA.generic.services.utils import constants, decorators
from esp32OTA.DeviceManagement.controllers.DeviceTypeController import DeviceTypeController

device_type_bp = Blueprint("device_type_bp", __name__)


@device_type_bp.route("/create", methods=["POST"])
@decorators.is_authenticated
@decorators.keys_validator(
    constants.REQUIRED_FIELDS_LIST__DEVICE_TYPE,
    constants.OPTIONAL_FIELDS_LIST__DEVICE_TYPE,
    request_form_data=True
)
def create_view(data):
    return DeviceTypeController.create_controller(data=data)


@device_type_bp.route("/read", methods=["GET", "POST"])
@decorators.is_authenticated
@decorators.keys_validator()
def read_view(data):
    return DeviceTypeController.read_controller(data=data)


@device_type_bp.route("/update", methods=["PUT"])
@decorators.is_authenticated
@decorators.keys_validator()
def update_view(data):
    return DeviceTypeController.update_controller(data=data)


@device_type_bp.route("/suspend", methods=["PUT"])
@decorators.is_authenticated
@decorators.keys_validator()
def suspend_view(data):
    return DeviceTypeController.suspend_controller(data=data)
