# Framework Imports
from flask import jsonify

from esp32OTA.generic.services.utils import response_codes


def get_response_object(response_code=response_codes.CODE_SUCCESS, response_data=None,
                        response_message=response_codes.MESSAGE_SUCCESS):

    response = {
        "response_code": response_code
    }
    if response_data is not None:
        response.update({
            "response_data": response_data
        })
    if response_message:
        response.update({
            "response_message": response_message
        })

    # return jsonify(response)
    return response

def get_json_response_object(response_code=response_codes.CODE_SUCCESS, response_data=None,
                        response_message=response_codes.MESSAGE_SUCCESS):

    response = {
        "response_code": response_code
    }
    if response_data is not None:
        response.update({
            "response_data": response_data
        })
    if response_message:
        response.update({
            "response_message": response_message
        })

    return jsonify(response)
    # return response