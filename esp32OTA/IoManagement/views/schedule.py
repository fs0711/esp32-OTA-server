# Python imports
import os
import re
from datetime import datetime
# Framework imports
from flask import Blueprint, redirect, url_for, redirect, render_template, request

# Local imports
from esp32OTA.IoManagement.controllers.ScheduleController import ScheduleController
from esp32OTA.generic.services.utils import constants, decorators, common_utils
from esp32OTA.config import config

schedule_bp = Blueprint("schedule_bp", __name__)


@schedule_bp.route("/create", methods=["POST"])
@decorators.is_authenticated
@decorators.keys_validator(
    constants.REQUIRED_FIELDS_LIST__SCHEDULE,
    request_form_data=False
)
def create_view(data):
    return ScheduleController.create_controller(data=data)


@schedule_bp.route("/read", methods=["GET", "POST"])
@decorators.is_authenticated
@decorators.keys_validator()
def read_view(data):
    if request.method == "POST":
        data = request.form
    return ScheduleController.read_controller(data=data)


@schedule_bp.route("/update", methods=["PUT"])
@decorators.is_authenticated
# @decorators.roles_allowed([constants.ROLE_ID_ADMIN])
@decorators.keys_validator()
def update_view(data):
    return ScheduleController.update_controller(data=data)

@schedule_bp.route("/search", methods=["POST", "GET"])
@decorators.is_authenticated
@decorators.keys_validator()
def search_view(data):
    return ScheduleController.search_controller(data=data)
