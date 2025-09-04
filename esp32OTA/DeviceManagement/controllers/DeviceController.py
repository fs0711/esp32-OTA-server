# Python imports
import re
from math import nan, isnan
# Framework imports

# Local imports
from ast import Constant
from esp32OTA.generic.controllers import Controller
from esp32OTA.DeviceManagement.models.Device import Device
from esp32OTA.UserManagement.controllers.TokenController import TokenController
from esp32OTA.UserManagement.controllers.UserController import UserController
from esp32OTA.generic.services.utils import constants, response_codes, response_utils, common_utils, pipeline
from esp32OTA import config
from datetime import datetime


class DeviceController(Controller):
    Model = Device

    @classmethod
    def create_controller(cls, data):
        is_valid, error_messages = cls.cls_validate_data(data=data)
        if not is_valid:
            return response_utils.get_response_object(
                response_code=response_codes.CODE_VALIDATION_FAILED,
                response_message=response_codes.MESSAGE_VALIDATION_FAILED,
                response_data=error_messages
            )
        user = common_utils.current_user()
        #generate access token for device 
        token_is_valid, token_error_messages, token = TokenController.generate_access_token(purpose=constants.PURPOSE_LOGIN, 
                                                                                            platform=constants.PLATFORM_DEVICE, 
                                                                                            expiry_time=config.TOKEN_EXPIRY_TIME_DEVICE,
                                                                                            user=user)
        if token_is_valid:
            data.update({constants.DEVICE__ACCESS_TOKEN:token[constants.TOKEN__ACCESS_TOKEN]})
            _, _, obj = cls.db_insert_record(
                data=data, default_validation=False)
            return response_utils.get_response_object(
                response_code=response_codes.CODE_SUCCESS,
                response_message=response_codes.MESSAGE_SUCCESS,
                response_data=obj.display()
            )
        return response_utils.get_response_object(
            response_code=response_codes.CODE_CREATE_FAILED,
            response_message=response_codes.MESSAGE_OPERATION_FAILED,
            response_data=token_error_messages
        )

    @classmethod
    def read_controller(cls, data):
        user_childs =  UserController.get_users_childs_list()
        filter = {}
        filter[constants.DEVICE__ORGANIZATION+"__in"] = [id[constants.USER__ORGANIZATION][constants.ID] for id in user_childs]

        return response_utils.get_response_object(
            response_code=response_codes.CODE_SUCCESS,
            response_message=response_codes.MESSAGE_SUCCESS,
            response_data=[
                obj.display() for obj in cls.db_read_records(read_filter=filter, deleted_records=False)
            ])


    @classmethod
    def update_controller(cls, data):
        is_valid, error_messages, obj = cls.db_update_single_record(
            read_filter={constants.ID: data[constants.ID]}, update_filter=data
        )
        if not is_valid:
            return response_utils.get_response_object(
                response_code=response_codes.CODE_VALIDATION_FAILED,
                response_message=response_codes.MESSAGE_VALIDATION_FAILED,
                response_data=error_messages
            )
        if not obj:
            return response_utils.get_response_object(
                response_code=response_codes.CODE_RECORD_NOT_FOUND,
                response_message=response_codes.MESSAGE_NOT_FOUND_DATA.format(
                    constants.DEVICE.title(), constants.ID
                ))
        return response_utils.get_response_object(
            response_code=response_codes.CODE_SUCCESS,
            response_message=response_codes.MESSAGE_SUCCESS,
            response_data=obj.display(),
        )


    @classmethod
    def suspend_controller(cls, data):
        _, _, obj = cls.db_update_single_record(
            read_filter={constants.ID: data[constants.ID]},
            update_filter={
                constants.STATUS: constants.OBJECT_STATUS_SUSPENDED},
            update_mode=constants.UPDATE_MODE__PARTIAL,
        )
        if obj:
            return response_utils.get_response_object(
                response_code=response_codes.CODE_SUCCESS,
                response_message=response_codes.MESSAGE_SUCCESS,
                response_data=obj.display(),
            )
        return response_utils.get_response_object(
            response_code=response_codes.CODE_RECORD_NOT_FOUND,
            response_message=response_codes.MESSAGE_NOT_FOUND_DATA.format(
                constants.DEVICE.title(), constants.ID
            ))