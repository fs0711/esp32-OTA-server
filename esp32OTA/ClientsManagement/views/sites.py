# Python imports
import os
import re
from datetime import datetime
# Framework imports
from flask import Blueprint, request

# Local imports
from esp32OTA.ClientsManagement.controllers.SitesController import SitesController
from esp32OTA.generic.services.utils import constants, decorators, common_utils
from esp32OTA.config import config

sites_bp = Blueprint("sites_bp", __name__)


@sites_bp.route("/create", methods=["POST"])
@decorators.is_authenticated
@decorators.keys_validator(
    constants.REQUIRED_FIELDS_LIST__SITE,
    constants.OPTIONAL_FIELDS_LIST__SITE,
    request_form_data=False
)
def create_view(data):
    return SitesController.create_controller(data=data)


@sites_bp.route("/read", methods=["GET", "POST"])
@decorators.is_authenticated
@decorators.keys_validator()
def read_view(data):
    if request.method == "POST":
        data = request.form
    return SitesController.read_controller(data=data)


@sites_bp.route("/getsites", methods=["GET"])
@decorators.is_authenticated
# @decorators.keys_validator()
def get_view():
    return SitesController.get_clients()


@sites_bp.route("/update", methods=["PUT"])
@decorators.is_authenticated
# @decorators.roles_allowed([constants.ROLE_ID_ADMIN])
@decorators.keys_validator()
def update_view(data):
    return SitesController.update_controller(data=data)

@sites_bp.route("/search", methods=["POST", "GET"])
@decorators.is_authenticated
@decorators.keys_validator()
def search_view(data):
    return SitesController.search_controller(data=data)
