# Python imports
import re
from math import nan, isnan
# Framework imports

# Local imports
from ast import Constant
from esp32OTA.generic.controllers import Controller
from esp32OTA.FirmwareManagement.models.Firmware import Firmware
from esp32OTA.generic.services.utils import constants, response_codes, response_utils, common_utils, pipeline


class FirmwareController(Controller):
    Model = Firmware

    @classmethod
    def upload_controller(cls, data):
        is_valid, error_messages = cls.cls_validate_data(data=data)
        if not is_valid:
            return response_utils.get_response_object(
                response_code=response_codes.CODE_VALIDATION_FAILED,
                response_message=response_codes.MESSAGE_VALIDATION_FAILED,
                response_data=error_messages
            )
        _, _, obj = cls.db_insert_file(
            data=data, default_validation=False)
        return response_utils.get_response_object(
            response_code=response_codes.CODE_SUCCESS,
            response_message=response_codes.MESSAGE_SUCCESS
        )


    @classmethod
    def read_controller(cls, data):
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
    
    @classmethod
    def upload_bin_to_gridfs(cls, file_obj, filename, metadata=None):
        """
        Uploads a .bin file to MongoDB GridFS using mongoengine.

        Args:
            file_obj: File-like object containing binary data.
            filename: Name to store in GridFS.
            metadata: Optional dict of metadata.

        Returns:
            firmware: The Firmware document instance.
        """
        firmware = Firmware()
        firmware.bin_file.put(file_obj, filename=filename)
        if metadata:
            for key, value in metadata.items():
                setattr(firmware, key, value)
        firmware.save()
        return firmware