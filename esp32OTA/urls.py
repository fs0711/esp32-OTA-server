# Python imports

# Framework imports
from flask import jsonify, render_template


# Local imports
from esp32OTA import app, config
from esp32OTA.generic.services.utils import constants, decorators, response_utils, common_utils
from esp32OTA.UserManagement.views.users import users_bp
from esp32OTA.DeviceManagement.views.device import device_bp
from esp32OTA.DeviceManagement.views.device_type import device_type_bp
from esp32OTA.FirmwareManagement.views.firmware import firmware_bp


@app.route("/api/static-data", methods=["GET"])
def static_data_view():
    return jsonify(constants.STATIC_DATA)



app.register_blueprint(users_bp, url_prefix="/api/users")
app.register_blueprint(device_bp, url_prefix="/api/device")
app.register_blueprint(device_type_bp, url_prefix="/api/device-type")
app.register_blueprint(firmware_bp, url_prefix="/api/firmware")
