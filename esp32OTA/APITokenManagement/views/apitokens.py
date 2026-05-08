# Python imports

# Framework imports
from flask import Blueprint, request

# Local imports
from esp32OTA.APITokenManagement.controllers.APITokenController import APITokenController
from esp32OTA.generic.services.utils import response_utils, response_codes, decorators, constants


api_token_bp = Blueprint('api_token_management', __name__)


@api_token_bp.route('/create', methods=['POST'])
@decorators.is_authenticated
@decorators.keys_validator(
    ['service_name'],
    []
)
def create_api_token_view(data):
    return APITokenController.create_controller(data=data)


@api_token_bp.route('/list', methods=['GET'])
@decorators.is_authenticated
@decorators.keys_validator(
    [],
    ['id', 'service_name', 'is_active']
)
def list_api_tokens_view(data):
    return APITokenController.read_controller(data=data)


@api_token_bp.route('/suspend', methods=['POST'])
@decorators.is_authenticated
@decorators.keys_validator(
    [],
    ['access_token', 'id']
)
def suspend_api_token_view(data):
    return APITokenController.suspend_controller(data=data)


@api_token_bp.route('/delete', methods=['POST'])
@decorators.is_authenticated
@decorators.keys_validator(
    [],
    ['access_token', 'id']
)
def delete_api_token_view(data):
    return APITokenController.delete_controller(data=data)
