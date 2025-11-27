# Python imports
import re
from math import nan, isnan
# Framework imports
from flask import Response, stream_with_context

# Local imports
from ast import Constant
from esp32OTA.generic.controllers import Controller
from esp32OTA.FirmwareManagement.models.Firmware import Firmware
from esp32OTA.DeviceManagement.models.Device import Device
from esp32OTA.DeviceManagement.models.DeviceType import DeviceType
from esp32OTA.generic.services.utils import constants, response_codes, response_utils, common_utils, pipeline


class FirmwareController(Controller):
    Model = Firmware # type: ignore[assignment]

    @classmethod
    def upload_controller(cls, data):
        is_valid, error_messages = cls.cls_validate_data(data=data)
        if not is_valid:
            return response_utils.get_response_object(
                response_code=response_codes.CODE_VALIDATION_FAILED,
                response_message=response_codes.MESSAGE_VALIDATION_FAILED,
                response_data=error_messages
            )
        checksum_in = data[constants.FIRMWARE__CHECKSUM]
        checksum = common_utils.get_file_checksum(data[constants.FIRMWARE__FILE])
        if checksum != checksum_in:
            return response_utils.get_response_object(
                response_code=response_codes.CODE_VALIDATION_FAILED,
                response_message=response_codes.MESSAGE_INVALID_CHECKSUM.format(checksum_in, checksum),
                response_data=[]
            )
        data[constants.FIRMWARE__CHECKSUM] = checksum
        _, _, obj = cls.db_insert_file(
            data=data, default_validation=False)
        return response_utils.get_response_object(
            response_code=response_codes.CODE_SUCCESS,
            response_message=response_codes.MESSAGE_SUCCESS,
            response_data=obj.display()
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
    def assign_firmware_to_device_type(cls, data):

        firmware_id = data.get(constants.ID)
        device_type_id = data.get(constants.DEVICE_TYPE__ID)
        
        if not firmware_id or not device_type_id:
            return response_utils.get_response_object(
                response_code=response_codes.CODE_VALIDATION_FAILED,
                response_message=response_codes.MESSAGE_VALIDATION_FAILED,
                response_data=["firmware_id and device_type_id are required"]
            )
        
        # Get firmware object
        firmware = cls.db_read_single_record(
            read_filter={constants.ID: firmware_id},
            deleted_records=False
        )
        
        if not firmware:
            return response_utils.get_response_object(
                response_code=response_codes.CODE_RECORD_NOT_FOUND,
                response_message=response_codes.MESSAGE_NOT_FOUND_DATA.format(
                    constants.FIRMWARE.title(), constants.ID
                ))
        
        # Get device type object
        device_type = DeviceType.objects(
            id=device_type_id,
            status=constants.OBJECT_STATUS_ACTIVE
        ).first()
        
        if not device_type:
            return response_utils.get_response_object(
                response_code=response_codes.CODE_RECORD_NOT_FOUND,
                response_message=response_codes.MESSAGE_NOT_FOUND_DATA.format(
                    constants.DEVICE_TYPE.title(), constants.ID
                ))
        
        # Assign firmware to device type
        firmware.update(set__device_type=device_type)
        firmware.reload()
        
        # Find all devices matching device type and hardware version
        device_filter = {
            constants.DEVICE__TYPE: device_type,
            constants.STATUS: constants.OBJECT_STATUS_ACTIVE
        }
        
        # If firmware has hardware version, filter by it
        if firmware.hw_version:
            device_filter[constants.DEVICE__HARDWARE_VERSION] = firmware.hw_version
        
        # Update all matching devices
        devices = Device.objects(**device_filter)
        updated_count = 0
        
        for device in devices:
            device.update(
                set__new_fw_version=firmware.version,
                set__update_path=firmware.update_path if firmware.update_path else None,
                set__fw_file=firmware
            )
            updated_count += 1
        
        return response_utils.get_response_object(
            response_code=response_codes.CODE_SUCCESS,
            response_message=response_codes.MESSAGE_SUCCESS,
            response_data={
                "firmware": firmware.display(),
                "device_type": device_type.display_min(),
                "devices_updated": updated_count
            }
        )
    
    @classmethod
    def download_firmware(cls, data):
        try:
            # Retrieve firmware record
            firmware = Firmware.objects(
                id=data[constants.ID],
                status=constants.OBJECT_STATUS_ACTIVE
            ).first()
            
            if not firmware:
                return response_utils.get_response_object(
                    response_code=response_codes.CODE_RECORD_NOT_FOUND,
                    response_message=response_codes.MESSAGE_NOT_FOUND_DATA.format(
                        constants.FIRMWARE.title(), constants.ID
                    ))
            
            # Check if file exists
            if not firmware.file:
                return response_utils.get_response_object(
                    response_code=response_codes.CODE_RECORD_NOT_FOUND,
                    response_message="Firmware file not found"
                )
            
            # Create a generator to stream the file in chunks
            def generate():
                chunk_size = 4096  # 4KB chunks
                firmware.file.seek(0)
                while True:
                    chunk = firmware.file.read(chunk_size)
                    if not chunk:
                        break
                    yield chunk
            
            # Get filename for the download
            filename = firmware.file_name if firmware.file_name else f"firmware_{firmware.version}.bin"
            
            # Create streaming response
            response = Response(
                stream_with_context(generate()),
                mimetype='application/octet-stream'
            )
            
            # Set headers for file download
            response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
            response.headers['Content-Type'] = 'application/octet-stream'
            response.headers['Content-Length'] = str(firmware.file.length)
            response.headers['X-Firmware-Version'] = firmware.version
            response.headers['X-Firmware-Checksum'] = firmware.checksum
            
            if firmware.hw_version:
                response.headers['X-Hardware-Version'] = firmware.hw_version
            
            return response
            
        except Exception as e:
            return response_utils.get_response_object(
                response_code=response_codes.CODE_EXCEPTION,
                response_message=f"Error downloading firmware: {str(e)}"
            )

