# Python imports
import os
import re
from datetime import datetime
# Framework imports
from flask import Blueprint, redirect, url_for, redirect, render_template, request

# Local imports
from esp32OTA.IoManagement.controllers.IoController import IoController
from esp32OTA.generic.services.utils import constants, decorators, common_utils
from esp32OTA.config import config

io_bp = Blueprint("io_bp", __name__)


@io_bp.route("/create", methods=["POST"])
@decorators.is_authenticated
@decorators.keys_validator(
    constants.REQUIRED_FIELDS_LIST__IO,
    constants.OPTIONAL_FIELDS_LIST__IO,
    request_form_data=False
)
def create_view(data):
    return IoController.create_controller(data=data)


@io_bp.route("/read", methods=["GET", "POST"])
@decorators.is_authenticated
@decorators.keys_validator(
    [constants.ID]
)
def read_view(data):
    return IoController.read_controller(data=data)


@io_bp.route("/update", methods=["PUT"])
@decorators.is_authenticated
# @decorators.roles_allowed([constants.ROLE_ID_ADMIN])
@decorators.keys_validator()
def update_view(data):
    return IoController.update_controller(data=data)

@io_bp.route("/search", methods=["POST", "GET"])
@decorators.is_authenticated
@decorators.keys_validator()
def search_view(data):
    return IoController.search_controller(data=data)
