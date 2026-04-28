# Python imports

# Framework imports
from flask import Blueprint, request, jsonify

# Local imports
from esp32OTA.generic.services.utils import constants, decorators, response_codes
from esp32OTA.DeviceManagement.controllers.MQTTAuthController import MQTTAuthController

mqtt_auth_bp = Blueprint("mqtt_auth_bp", __name__)


def _mqtt_json_response(result):
    """
    Convert a controller result dict to an MQTT auth JSON response.
    Returns {"Ok": bool, "Error": str} with the appropriate HTTP status code.
    """
    success = result.get("response_code") == response_codes.CODE_SUCCESS
    error_msg = "" if success else result.get("response_message", "Unauthorized")
    http_status = 200 if success else 401
    return jsonify({"Ok": success, "Error": error_msg}), http_status


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
    result = MQTTAuthController.authenticate_mqtt_controller(data=data)
    return _mqtt_json_response(result)


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
    result = MQTTAuthController.authenticate_mqtt_superuser_controller(data=data)
    return _mqtt_json_response(result)


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
    result = MQTTAuthController.authorize_mqtt_acl_controller(data=data)
    return _mqtt_json_response(result)
