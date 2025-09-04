# Python imports
import re
from math import nan, isnan
# Framework imports

# Local imports
from ast import Constant
from esp32OTA.generic.controllers import Controller
from esp32OTA.IoManagement.models.Io import Io
from esp32OTA.DeviceManagement.controllers.DeviceController import DeviceController
from esp32OTA.generic.services.utils import constants, response_codes, response_utils, common_utils, pipeline


class IoController(Controller):
    Model = Io

    @classmethod
    def create_controller(cls, data):
        is_valid, error_messages = cls.cls_validate_data(data=data)
        if not is_valid:
            return response_utils.get_response_object(
                response_code=response_codes.CODE_VALIDATION_FAILED,
                response_message=response_codes.MESSAGE_VALIDATION_FAILED,
                response_data=error_messages
            )
        is_valid, error, io_obj = cls.db_insert_record(
            data=data, default_validation=False)
        if is_valid:
            if data[constants.IO__TYPE] == constants.IO__TYPE_LIST[0]:
                device = DeviceController.db_read_single_record(read_filter={constants.ID:data[constants.IO__DEVICE]})[constants.DEVICE__INPUTS].copy()
                device.append({"id":str(io_obj[constants.ID]),"name":data[constants.IO__NAME], "display":data[constants.IO__DISPLAY] if data.get(constants.IO__DISPLAY) else []})
                update_data = {constants.DEVICE__INPUTS:device}
            if data[constants.IO__TYPE] == constants.IO__TYPE_LIST[1]:
                device = DeviceController.db_read_single_record(read_filter={constants.ID:data[constants.IO__DEVICE]})[constants.DEVICE__OUTPUTS].copy()
                device.append({"id":str(io_obj[constants.ID]),"name":data[constants.IO__NAME], "display":data[constants.IO__DISPLAY] if data.get(constants.IO__DISPLAY) else []})
                update_data = {constants.DEVICE__OUTPUTS:device}
            if data[constants.IO__TYPE] == constants.IO__TYPE_LIST[2]:
                device = DeviceController.db_read_single_record(read_filter={constants.ID:data[constants.IO__DEVICE]})[constants.DEVICE__VARIABLES].copy()
                device.append({"id":str(io_obj[constants.ID]),"name":data[constants.IO__NAME], "display":data[constants.IO__DISPLAY] if data.get(constants.IO__DISPLAY) else []})
                update_data = {constants.DEVICE__VARIABLES:device}
            is_valid, error, device_obj = DeviceController.db_update_single_record(read_filter={constants.ID:data[constants.IO__DEVICE]},
                                                                                   update_filter=update_data)
            if is_valid:
                return response_utils.get_response_object(
                    response_code=response_codes.CODE_SUCCESS,
                    response_message=response_codes.MESSAGE_SUCCESS,
                    response_data=io_obj.display()
                )
            return response_utils.get_response_object(
                response_code=response_codes.CODE_CREATE_FAILED,
                response_message=response_codes.MESSAGE_OPERATION_FAILED,
                response_data=error
            )
        return response_utils.get_response_object(
            response_code=response_codes.CODE_CREATE_FAILED,
            response_message=response_codes.MESSAGE_OPERATION_FAILED,
            response_data=error
        )


    @classmethod
    def read_controller(cls, data):
        return response_utils.get_response_object(
            response_code=response_codes.CODE_SUCCESS,
            response_message=response_codes.MESSAGE_SUCCESS,
            response_data=[
                obj.display() for obj in cls.db_read_records(read_filter=data, deleted_records=False)
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
                    constants.IO.title(), constants.ID
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
                constants.IO.title(), constants.ID
            ))
    
    @classmethod
    def get_types_controller(cls, data):
        obj = cls.db_read_single_record(read_filter=data)
        return obj.display_types()