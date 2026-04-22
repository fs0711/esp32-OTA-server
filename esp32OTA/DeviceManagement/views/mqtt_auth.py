# Python imports

# Framework imports
from flask import Blueprint, request

# Local imports
from esp32OTA.generic.services.utils import constants, decorators
from esp32OTA.DeviceManagement.controllers.MQTTAuthController import MQTTAuthController

mqtt_auth_bp = Blueprint("mqtt_auth_bp", __name__)


@mqtt_auth_bp.route("/auth", methods=["POST"])
@decorators.keys_validator(
    ['username', 'password'],
    [],
    request_form_data=True
)
def mqtt_auth_view(data):
    """
    MQTT Authentication endpoint
    Accepts username (device_id) and password (HMAC token)
    Returns authentication result
    """
    return MQTTAuthController.authenticate_mqtt_controller(data=data)


@mqtt_auth_bp.route("/superuser", methods=["POST"])
@decorators.keys_validator(
    ['username'],
    [],
    request_form_data=True
)
def mqtt_superuser_view(data):
    """
    MQTT Superuser check endpoint
    Accepts username and returns whether user is a superuser
    """
    return MQTTAuthController.authenticate_mqtt_superuser_controller(data=data)


@mqtt_auth_bp.route("/acl", methods=["POST"])
@decorators.keys_validator(
    ['username', 'topic'],
    ['acc', 'clientid'],
    request_form_data=True
)
def mqtt_acl_view(data):
    """
    MQTT ACL (Access Control List) endpoint
    Accepts username, topic, and access type
    Returns authorization result
    """
    return MQTTAuthController.authorize_mqtt_acl_controller(data=data)
