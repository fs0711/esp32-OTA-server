# Python imports
import re
from math import nan, isnan
# Framework imports

# Local imports
from ast import Constant
from esp32OTA.generic.controllers import Controller
from esp32OTA.DeviceManagement.models.Device import Device
from esp32OTA.DeviceManagement.models.DeviceType import DeviceType
from esp32OTA.UserManagement.controllers.TokenController import TokenController
from esp32OTA.UserManagement.controllers.UserController import UserController
from esp32OTA.generic.services.utils import constants, response_codes, response_utils, common_utils, __global__
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
        
        # Get device type to retrieve type_code
        device_type_obj = DeviceType.objects(
            device_type=data.get(constants.DEVICE__TYPE),
            status=constants.OBJECT_STATUS_ACTIVE
        ).first()
        
        if not device_type_obj:
            return response_utils.get_response_object(
                response_code=response_codes.CODE_RECORD_NOT_FOUND,
                response_message=response_codes.MESSAGE_NOT_FOUND_DATA.format(
                    "Device Type", constants.DEVICE__TYPE
                ),
                response_data=[]
            )
        
        data[constants.DEVICE__TYPE] = device_type_obj.id
        user = common_utils.current_user()
        #generate access token for device 
        token_is_valid, token_error_messages, token = TokenController.generate_access_token(purpose=constants.PURPOSE_LOGIN, 
                                                                                            platform=constants.PLATFORM_DEVICE, 
                                                                                            expiry_time=config.TOKEN_EXPIRY_TIME_DEVICE,
                                                                                            user=user)
        if token_is_valid:
            data.update({constants.DEVICE__ACCESS_TOKEN:token[constants.TOKEN__ACCESS_TOKEN]})
            
            # Create device to get unique ID (device_id)
            _, _, obj = cls.db_insert_record(
                data=data, default_validation=False)
            
            # Generate serial number using type_code and device_id
            type_code = device_type_obj.type_code
            # Extract numeric part from device_id (format: DV-XXX)
            device_numeric_id = int(obj.device_id.split('-')[1]) if '-' in str(obj.device_id) else obj.id
            serial_number = common_utils.generate_device_serial(type_code, device_numeric_id)
            
            # Update device with serial number
            obj.update(set__serial_number=serial_number)
            obj.save()
            
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

        return response_utils.get_response_object(
            response_code=response_codes.CODE_SUCCESS,
            response_message=response_codes.MESSAGE_SUCCESS,
            response_data=[
                obj.display() for obj in cls.db_read_records(read_filter=filter, deleted_records=False)
            ])


    @classmethod
    def update_controller(cls, data):
        # Get device type to retrieve type_code
        device_type_obj = DeviceType.objects(
            device_type=data.get(constants.DEVICE__TYPE),
            status=constants.OBJECT_STATUS_ACTIVE
        ).first()
        
        if not device_type_obj:
            return response_utils.get_response_object(
                response_code=response_codes.CODE_RECORD_NOT_FOUND,
                response_message=response_codes.MESSAGE_NOT_FOUND_DATA.format(
                    "Device Type", constants.DEVICE__TYPE
                ),
                response_data=[]
            )
        
        data[constants.DEVICE__TYPE] = device_type_obj.id

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
    
    @classmethod
    def get_device_by_access_token(cls, access_token):
        device_obj = cls.db_read_single_record(
            read_filter={constants.DEVICE__ACCESS_TOKEN: access_token,
                         constants.STATUS: constants.OBJECT_STATUS_ACTIVE}
        )
        return device_obj
    
    @classmethod
    def config_controller(cls, data, method):
        device = __global__.get_current_device()
        if device is not None:
            if method == "GET":
                obj = cls.db_read_single_record(
                    read_filter={constants.ID: device[constants.ID]}
                )
                if obj:
                    return response_utils.get_response_object(
                        response_code=response_codes.CODE_SUCCESS,
                        response_message=response_codes.MESSAGE_SUCCESS,
                        response_data=obj.display_config(),
                    )
                else:
                    return response_utils.get_response_object(
                        response_code=response_codes.CODE_RECORD_NOT_FOUND,
                        response_message=response_codes.MESSAGE_NOT_FOUND_DATA.format(
                            constants.DEVICE.title(), constants.ID
                        ))
            if method == "POST":
                is_valid, error_messages, obj = cls.db_update_single_record(
                    read_filter={constants.ID: device[constants.ID]},
                    update_filter=data,
                    update_mode=constants.UPDATE_MODE__PARTIAL,
                )
                if not is_valid:
                    return response_utils.get_response_object(
                        response_code=response_codes.CODE_VALIDATION_FAILED,
                        response_message=response_codes.MESSAGE_VALIDATION_FAILED,
                        response_data=error_messages
                    )
                obj.save()
                return response_utils.get_response_object(
                    response_code=response_codes.CODE_SUCCESS,
                    response_message=response_codes.MESSAGE_SUCCESS,
                    response_data=obj.display_config(),
                )
        return response_utils.get_response_object(
            response_code=response_codes.CODE_RECORD_NOT_FOUND,
            response_message=response_codes.MESSAGE_NOT_FOUND_DATA.format(
                constants.DEVICE.title(), constants.ID
            ))