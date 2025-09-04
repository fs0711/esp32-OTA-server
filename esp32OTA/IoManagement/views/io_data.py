# Python imports
import os
import re
from datetime import datetime
# Framework imports
from flask import Blueprint, redirect, url_for, redirect, render_template, request

# Local imports
from esp32OTA.IoManagement.controllers.Io_dataController import Io_dataController
from esp32OTA.generic.services.utils import constants, decorators, common_utils
from esp32OTA.config import config

io_data_bp = Blueprint("io_data_bp", __name__)


@io_data_bp.route("/update", methods=["POST"])
@decorators.is_authenticated
@decorators.keys_validator(
    constants.REQUIRED_FIELDS_LIST__IO_DATA,
    constants.OPTIONAL_FIELDS_LIST__IO_DATA,
    request_form_data=False
)
def create_view(data):
    return Io_dataController.create_controller(data=data)

@io_data_bp.route("/status", methods=["POST"])
@decorators.is_authenticated
@decorators.keys_validator(
    [constants.IO_DATA__ID],
    request_form_data=False
)
def status_view(data):
    return Io_dataController.status_controller(data=data)


@io_data_bp.route("/read", methods=["GET", "POST"])
@decorators.is_authenticated
@decorators.keys_validator()
def read_view(data):
    if request.method == "POST":
        data = request.form
    return Io_dataController.read_controller(data=data)

@io_data_bp.route("/read_last", methods=["POST"])
@decorators.is_authenticated
@decorators.keys_validator(
    [constants.ID]
)
def read_last_view(data):
    return Io_dataController.read_last(data=data)


@io_data_bp.route("/trigger", methods=["POST"])
@decorators.is_authenticated
@decorators.keys_validator(
    [constants.ID, constants.IO_DATA__DATA],
    request_form_data=False
)
def trigger_view(data):
    return Io_dataController.trigger_controller(data=data)