# Python imports

# Framework imports
from flask import Blueprint, request

# Local imports
from esp32OTA.TokenManagement.controllers.TokenController import TokenController
from esp32OTA.generic.services.utils import response_utils, response_codes, decorators, constants


token_mgmt_bp = Blueprint('token_management', __name__)


@token_mgmt_bp.route('/generate', methods=['POST'])
@decorators.is_authenticated
@decorators.keys_validator(
    [constants.TOKEN__SERVICE_NAME],
    []
)
def generate_token_view(data):
    return TokenController.create_controller(data=data)

