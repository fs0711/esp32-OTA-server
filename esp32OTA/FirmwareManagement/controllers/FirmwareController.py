# Python imports
import re
import os
import json
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
from esp32OTA.Services.mqtt_client import mqtt_service


class FirmwareController(Controller):
    Model = Firmware # type: ignore[assignment]

    @classmethod
    def upload_controller(cls, data):
        is_valid, error_messages = cls.cls_validate_data(data=data)
        filename = data[constants.FIRMWARE__FILE].filename
        data[constants.FIRMWARE__FILE_NAME] = re.sub(r'[^a-zA-Z0-9_.-]', '_', filename)
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
        
        # Save firmware file to local storage
        if obj:
            # Create firmware_files directory if it doesn't exist
            firmware_dir = os.path.join(os.getcwd(), 'firmware_files')
            os.makedirs(firmware_dir, exist_ok=True)
            
            # Save file with record ID as filename
            firmware_file = data[constants.FIRMWARE__FILE]
            firmware_file.seek(0)  # Reset file pointer to beginning
            file_path = os.path.join(firmware_dir, str(obj.id))
            
            with open(file_path, 'wb') as f:
                f.write(firmware_file.read())
        
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
    def update_controller(cls, data):
        _, _, obj = cls.db_update_single_record(
            read_filter={constants.ID: data[constants.ID]},
            update_filter=data,
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
                constants.FIRMWARE.title(), constants.ID
            ))

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
        
        # Get firmware objectt
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

            # Prepare MQTT payload for the device with shortened keys
            import time
            mqtt_payload = {
                "t": int(time.time()),
                "f_f": str(firmware.file_name) if firmware.file_name else "",
                "f_v": str(device.fw_version) if device.fw_version else "",
                "h_v": str(device.hw_version) if device.hw_version else "",
                "n_v": str(firmware.version) if firmware.version else "",
                "u_p": str(firmware.update_path) if firmware.update_path else ""
            }
            
            # Publish to MQTT
            mqtt_service.publish_firmware_update(device.device_id, mqtt_payload)
        
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
            from flask import request, make_response
            firmware_id = data[constants.ID]
            
            # Retrieve firmware record
            firmware = Firmware.objects(
                id=firmware_id,
                status=constants.OBJECT_STATUS_ACTIVE
            ).first()

            if not firmware:
                return response_utils.get_response_object(
                    response_code=response_codes.CODE_RECORD_NOT_FOUND,
                    response_message=response_codes.MESSAGE_NOT_FOUND_DATA.format(
                        constants.FIRMWARE.title(), constants.ID
                    ))

            firmware_dir = os.path.join(os.getcwd(), 'firmware_files')
            file_path = os.path.join(firmware_dir, str(firmware_id))

            if not os.path.exists(file_path):
                if not firmware.file:
                    return response_utils.get_response_object(
                        response_code=response_codes.CODE_RECORD_NOT_FOUND,
                        response_message="Firmware file not found"
                    )
                os.makedirs(firmware_dir, exist_ok=True)
                firmware.file.seek(0)
                with open(file_path, 'wb') as f:
                    f.write(firmware.file.read())

            file_size = os.path.getsize(file_path)
            range_header = request.headers.get('Range', None)

            if range_header:
                match = re.match(r'bytes=(\d+)-(\d*)', range_header.strip())
                if match:
                    range_start = int(match.group(1))
                    range_end = match.group(2)
                    range_end = int(range_end) if range_end else file_size - 1
                    range_end = min(range_end, file_size - 1)

                    content_length = range_end - range_start + 1
                    
                    with open(file_path, 'rb') as f:
                        f.seek(range_start)
                        chunk = f.read(content_length)

                    response = make_response(chunk)
                    response.status_code = 206
                    response.headers.clear() # Clear any default headers
                    response.headers['Content-Type'] = 'application/octet-stream'
                    response.headers['Content-Range'] = f'bytes {range_start}-{range_end}/{file_size}'
                    response.headers['Content-Length'] = str(content_length)
                    response.headers['Accept-Ranges'] = 'bytes'
                    response.headers['Connection'] = 'close'
                    return response

            # Full file response
            with open(file_path, 'rb') as f:
                chunk = f.read()
            
            response = make_response(chunk, 200)
            response.headers['Content-Type'] = 'application/octet-stream'
            response.headers['Content-Length'] = str(file_size)
            response.headers['Accept-Ranges'] = 'bytes'
            return response

        except Exception as e:
            return response_utils.get_response_object(
                response_code=response_codes.CODE_EXCEPTION,
                response_message=f"Error downloading firmware: {str(e)}"
            )

        except Exception as e:
            return response_utils.get_response_object(
                response_code=response_codes.CODE_EXCEPTION,
                response_message=f"Error downloading firmware: {str(e)}"
            )

