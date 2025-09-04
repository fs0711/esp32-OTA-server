# Python imports

# Framework imports
from flask import jsonify, render_template


# Local imports
from esp32OTA import app, config
from esp32OTA.generic.services.utils import constants, decorators, response_utils, common_utils
from esp32OTA.UserManagement.views.users import users_bp
from esp32OTA.OrganizationsManagement.views.organizations import organizations_bp
from esp32OTA.ClientsManagement.views.clients import clients_bp
from esp32OTA.ClientsManagement.views.sites import sites_bp
from esp32OTA.DeviceManagement.views.device import device_bp
from esp32OTA.IoManagement.views.io import io_bp
from esp32OTA.IoManagement.views.io_data import io_data_bp
from esp32OTA.IoManagement.views.schedule import schedule_bp

from esp32OTA.UserManagement.controllers.UserController import UserController
from esp32OTA.IoManagement.controllers.Io_dataController import Io_dataController
from esp32OTA.DeviceManagement.controllers.DeviceController import DeviceController
from esp32OTA.IoManagement.controllers.IoController import IoController


@app.route("/api/static-data", methods=["GET"])
def static_data_view():
    return jsonify(constants.STATIC_DATA)

@app.route("/", methods=["GET"])
@decorators.logging
@decorators.keys_validator()
def logined_user_view(data):
    return render_template("login.html", Response=response_utils.get_response_object())


@app.route("/", methods=["POST"])
@decorators.logging
@decorators.keys_validator(
    constants.LOGIN_REQUIRED_FIELDS_LIST, 
    [],
    request_form_data=True
    )
def login_user_view(data):
    res = UserController.login_old_controller(data=data)
    return render_template("login.html", **res)

@app.route("/home", methods=["GET"])
# @decorators.logging
@decorators.is_authenticated
@decorators.keys_validator(
    []
)
def dashboard_view(data):
    devices = DeviceController.read_controller(data=data)
    for device in devices['response_data']:
        vars = device[constants.DEVICE__VARIABLES]
        inputs = device[constants.DEVICE__INPUTS]
        outputs = device[constants.DEVICE__OUTPUTS]
        vars_data = []
        inputs_data = []
        outputs_data = []
        for var in vars:
            data = {
                'id' : var["id"],
                'name': var['name'],
                'display':var['display']
            }
            types = IoController.get_types_controller(data={constants.ID:var[constants.ID]})
            obj = Io_dataController.read_controller(data={constants.IO_DATA__ID:data[constants.ID]})
            data.update({'data':obj['response_data']})
            data.update({'unit':types[constants.IO__UNIT],
                         'data_type':types[constants.IO__DATA_TYPE]})
            vars_data.append(data)
        for var in inputs:
            data = {
                'id' : var["id"],
                'name': var['name'],
                'display':var['display']
            }
            obj = Io_dataController.read_last(data={constants.IO_DATA__ID:data[constants.ID]})
            data.update({'data':obj['response_data']})
            inputs_data.append(data)
        for var in outputs:
            data = {
                'id' : var["id"],
                'name': var['name'],
                'display':var['display']
            }
            obj = Io_dataController.read_last(data={constants.IO_DATA__ID:data[constants.ID]})
            data.update({'data':obj['response_data']})
            outputs_data.append(data)
        device[constants.DEVICE__VARIABLES] = vars_data
        device[constants.DEVICE__OUTPUTS] = outputs_data
        device[constants.DEVICE__INPUTS] = inputs_data
        device[constants.DEVICE__LAST_UPDATED] = common_utils.get_last_update(device[constants.DEVICE__ACCESS_TOKEN])
    return render_template('dashboard.html', **devices)


@app.route("/reports", methods=["GET"])
# @decorators.logging
@decorators.is_authenticated
@decorators.keys_validator(
    []
)
def reports_view(data):
    devices = DeviceController.read_controller(data=data)
    for device in devices['response_data']:
        vars = device[constants.DEVICE__VARIABLES]
        # inputs = device[constants.DEVICE__INPUTS]
        # outputs = device[constants.DEVICE__OUTPUTS]
        vars_data = []
        # inputs_data = []
        # outputs_data = []
        for var in vars:
            data = {
                'id' : var["id"],
                'name': var['name'],
                'display':var['display']
            }
            obj = Io_dataController.read_controller(data={constants.IO_DATA__ID:data[constants.ID]})
            data.update({'data':obj['response_data']})
            vars_data.append(data)
        # for var in inputs:
        #     data = {
        #         'id' : var["id"],
        #         'name': var['name'],
        #         'display':var['display']
        #     }
        #     obj = Io_dataController.read_last(data={constants.IO_DATA__ID:data[constants.ID]})
        #     data.update({'data':obj['response_data']})
        #     inputs_data.append(data)
        # for var in outputs:
        #     data = {
        #         'id' : var["id"],
        #         'name': var['name'],
        #         'display':var['display']
        #     }
        #     obj = Io_dataController.read_last(data={constants.IO_DATA__ID:data[constants.ID]})
        #     data.update({'data':obj['response_data']})
        #     outputs_data.append(data)
        device[constants.DEVICE__VARIABLES] = vars_data
        # device[constants.DEVICE__OUTPUTS] = outputs_data
        # device[constants.DEVICE__INPUTS] = inputs_data
        # device[constants.DEVICE__LAST_UPDATED] = common_utils.get_last_update(device[constants.DEVICE__ACCESS_TOKEN])
    return render_template('reports.html', **devices)


app.register_blueprint(users_bp, url_prefix="/api/users")
app.register_blueprint(organizations_bp, url_prefix="/api/organizations")
app.register_blueprint(clients_bp, url_prefix="/api/clients")
app.register_blueprint(sites_bp, url_prefix="/api/sites")
app.register_blueprint(device_bp, url_prefix="/api/device")
app.register_blueprint(io_bp, url_prefix="/api/io")
app.register_blueprint(io_data_bp, url_prefix="/api/data")
app.register_blueprint(schedule_bp, url_prefix="/api/schedule")
