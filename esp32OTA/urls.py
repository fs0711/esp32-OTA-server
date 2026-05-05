# Python imports

# Framework imports
from flask import jsonify, render_template, request


# Local imports
from esp32OTA import app, config
from esp32OTA.Services.GatewayService import GatewayService
from esp32OTA.Services.ConfigController import ConfigController
from esp32OTA.generic.services.utils import constants, decorators, response_utils, common_utils
from esp32OTA.UserManagement.views.users import users_bp
from esp32OTA.DeviceManagement.views.device import device_bp
from esp32OTA.DeviceManagement.views.device_type import device_type_bp
from esp32OTA.DeviceManagement.views.mqtt_auth import mqtt_auth_bp
from esp32OTA.FirmwareManagement.views.firmware import firmware_bp
from esp32OTA.GatewayLogging.views.gateway_logging import gateway_logging_bp


@app.route("/api/static-data", methods=["GET"])
def static_data_view():
    return jsonify(constants.STATIC_DATA)


@app.route("/", methods=["GET"])
def login_page():
    return render_template("login.html")


@app.route("/gateway", methods=["GET"])
def gateway_dashboard():
    return render_template("index.html")


@app.route("/api/gateway/data", methods=["GET"])
def gateway_data():
    is_connected = GatewayService.get_mqtt_status()
    broker_stats = GatewayService.get_broker_stats()
    
    # Sort devices by ID for consistent display
    devices = sorted(GatewayService._last_data.values(), key=lambda x: x['id'])
    
    return jsonify({
        "mqtt_connected": is_connected,
        "broker_stats": broker_stats,
        "devices": devices
    })


@app.route("/api/gateway/logs", methods=["GET"])
def gateway_logs():
    logs = GatewayService.get_live_logs()
    return jsonify({"logs": logs})


@app.route("/api/gateway/config", methods=["GET", "POST"])
def gateway_config():
    if request.method == "GET":
        return ConfigController.get_config()
    
    data = common_utils.posted()
    return ConfigController.update_config(data)


app.register_blueprint(users_bp, url_prefix="/api/users")
app.register_blueprint(device_bp, url_prefix="/api/device")
app.register_blueprint(device_type_bp, url_prefix="/api/device-type")
app.register_blueprint(mqtt_auth_bp, url_prefix="/api/mqtt")
app.register_blueprint(firmware_bp, url_prefix="/api/firmware")
app.register_blueprint(gateway_logging_bp, url_prefix="/api/gateway-logging")