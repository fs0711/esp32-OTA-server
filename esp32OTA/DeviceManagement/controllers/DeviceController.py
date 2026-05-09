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
from esp32OTA.Services.mqtt_client import mqtt_service
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
            data.update({
                constants.DEVICE__CONNECTION: {
                    "status": "offline",
                    "last_update": "01-01-1970 00:00:00"
                },
                constants.DEVICE__ACCESS_TOKEN:token[constants.TOKEN__ACCESS_TOKEN]
            })
            
            # Create device to get unique ID (device_id)
            _, _, obj = cls.db_insert_record(
                data=data, default_validation=False)
            
            # Generate serial number using type_code and device_id
            type_code = device_type_obj.type_code
            # Extract numeric part from device_id (format: DV-XXX)
            device_id = obj.device_id
            device_numeric_id = int(obj.device_id.split('-')[1]) if '-' in str(obj.device_id) else obj.id
            serial_number = common_utils.generate_device_serial(type_code, device_numeric_id)
            
            # Update device with serial number
            if not data.get(constants.DEVICE__NAME):
                obj.update(set__name=device_id)
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
        # user_childs =  UserController.get_users_childs_list()
        filter = data

        return response_utils.get_response_object(
            response_code=response_codes.CODE_SUCCESS,
            response_message=response_codes.MESSAGE_SUCCESS,
            response_data=[
                obj.display() for obj in cls.db_read_records(read_filter=filter, deleted_records=False)
            ])

    @classmethod
    def read_min_controller(cls, data):
        # user_childs =  UserController.get_users_childs_list()
        filter = {}

        return response_utils.get_response_object(
            response_code=response_codes.CODE_SUCCESS,
            response_message=response_codes.MESSAGE_SUCCESS,
            response_data=[
                obj.display_min() for obj in cls.db_read_records(read_filter=filter, deleted_records=False)
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
        
        # Post to MQTT that configuration is updated
        topic = f"ZV/DEVICES/{obj.device_id}/config"
        mqtt_service.publish(topic, {"s": "update_required", "t": common_utils.get_time_iso()})

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
        
    @classmethod
    def get_last_online(cls):
        from esp32OTA.NotificationManagement.controller.NotificationsController import NotificationController
        devices = cls.db_read_records(
            read_filter={constants.STATUS: constants.OBJECT_STATUS_ACTIVE})
        for device in devices:
            online = common_utils.get_last_update(device[constants.DEVICE__ACCESS_TOKEN])
            if device[constants.DEVICE__CONNECTION]["status"] != online['status']:
                # Create notification for device status change
                notification_data = {
                    constants.NOTIFICATION__TITLE: f"Device {device[constants.DEVICE__NAME]} is now {online['status']}",
                    constants.NOTIFICATION__MESSAGE: f"The device '{device[constants.DEVICE__NAME]}' has changed its status to {online['status']} as of {online['last_update']}.",
                    constants.NOTIFICATION__TYPE: "device_status_change",
                    constants.NOTIFICATION__RELATED_DEVICE: str(device.id),
                }
                NotificationController.create_controller(notification_data)

    @classmethod
    def force_update_controller(cls, data):
        device_id_val = data.get(constants.ID)
        changes_required = data.get(constants.DEVICE__CHANGES_REQUIRED)

        # 1. Update update_config to true if changes_required is true
        if changes_required:
            is_valid, error_messages, obj = cls.db_update_single_record(
                read_filter={constants.ID: device_id_val},
                update_filter={constants.DEVICE__UPDATE_CONFIG: True},
                update_mode=constants.UPDATE_MODE__PARTIAL
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

            # 2. Post a payload on mqtt against device
            topic = f"ZV/DEVICES/{obj.device_id}/config_update"
            
            # Shorten variable names
            var_mapping = {
                "CT_CAL_HIGH": "cc_h",
                "CT_CAL_LOW": "cc_l",
                "CT_CAL_MID": "cc_m",
                "CT_MAX_CURRENT": "cmc",
                "VCAL": "vc",
                "app": "app",
                "app_password": "app_pwd",
                "app_user": "app_usr",
                "base_url": "burl",
                "bt_mac": "bt_m",
                "config_timeout": "cfg_to",
                "cut_A": "cut_a",
                "device_id": "did",
                "ime1": "ime1",
                "ping_api": "ping",
                "status_api": "status",
                "sw_timeout": "sw_to",
                "update_data_api": "update",
                "wifi_mac": "wifi_m",
                "wifi_password": "wifi_pwd",
                "wifi_ssid": "wifi_ssid"
            }
            
            shortened_variables = {}
            for key, value in obj.variables.items():
                short_key = var_mapping.get(key, key)
                shortened_variables[short_key] = value
            
            import time
            payload = {
                "t": int(time.time()),
                "variables": shortened_variables,
                "qr_code": obj.qr_code
            }
            
            try:
                mqtt_service.publish(topic, payload)
                # 3. If successful, change update_config back to false
                obj.update(set__update_config=False)
                obj.save()
            except Exception as e:
                return response_utils.get_response_object(
                    response_code=response_codes.CODE_OPERATION_FAILED,
                    response_message=f"MQTT Publish failed: {str(e)}",
                    response_data=[]
                )

            return response_utils.get_response_object(
                response_code=response_codes.CODE_SUCCESS,
                response_message="Force update triggered successfully",
                response_data=obj.display()
            )
        
        return response_utils.get_response_object(
            response_code=response_codes.CODE_VALIDATION_FAILED,
            response_message="changes_required must be true to trigger force update",
            response_data=[]
        )

    @classmethod
    def update_device_connection_status(cls):
        from esp32OTA.NotificationManagement.controller.NotificationsController import NotificationController
        devices = cls.db_read_records(
            read_filter={constants.STATUS: constants.OBJECT_STATUS_ACTIVE})
        for device in devices:
            online = common_utils.get_last_update(device[constants.DEVICE__ACCESS_TOKEN])
            if device[constants.DEVICE__CONNECTION]["status"] != online['status']:
                # Create notification for device status change
                notification_data = {
                    constants.NOTIFICATION__TITLE: f"Device {device[constants.DEVICE__NAME]} is now {online['status']}",
                    constants.NOTIFICATION__MESSAGE: f"The device '{device[constants.DEVICE__NAME]}' has changed its status to {online['status']} as of {online['last_update']}.",
                    constants.NOTIFICATION__TYPE: "device_status_change",
                    constants.NOTIFICATION__RELATED_DEVICE: str(device.id),
                }
                NotificationController.create_controller(notification_data)
            device[constants.DEVICE__CONNECTION] = online
            device.save()
        return True

    @classmethod
    def ping_controller(cls, data):
        """
        Sends a ping command to a device identified by client_id (c_s_id).
        The payload is sent exactly as provided via MQTT.
        
        Expected data format:
        {
            "c_s_id": 15,
            "s": [
                {
                    "status": 0,
                    "session_id": null,
                    "box_open_request": false,
                    "credit": 0.0
                }
            ]
        }
        """
        c_s_id = data.get("c_s_id")
        
        if not c_s_id:
            return response_utils.get_response_object(
                response_code=response_codes.CODE_VALIDATION_FAILED,
                response_message="c_s_id (client_id) is required",
                response_data=[]
            )
        
        # Find device by client_id
        device = Device.objects(client_id=str(c_s_id)).first()
        
        if not device:
            return response_utils.get_response_object(
                response_code=response_codes.CODE_RECORD_NOT_FOUND,
                response_message=f"Device with client_id {c_s_id} not found",
                response_data=[]
            )
        
        # Prepare the payload (the entire data dict) and post to MQTT
        topic = f"ZV/DEVICES/{device.device_id}/ping"
        
        try:
            mqtt_service.publish(topic, data)
            
            return response_utils.get_response_object(
                response_code=response_codes.CODE_SUCCESS,
                response_message="Ping sent successfully",
                response_data={
                    "device_id": str(device.device_id),
                    "client_id": c_s_id,
                    "topic": topic,
                    "payload": data
                }
            )
        except Exception as e:
            return response_utils.get_response_object(
                response_code=response_codes.CODE_OPERATION_FAILED,
                response_message=f"Failed to send ping: {str(e)}",
                response_data=[]
            )
    
    @classmethod
    def get_connected_devices_controller(cls, data):
        """
        Returns list of connected devices with their status and last_seen information.
        Only includes devices that have client_id and connection data.
        Response format:
        [
            {
                "device_id": "DV-2",
                "status": "online/offline",
                "last_seen": "2026-04-05T20:55:58+00:00"
            },
            ...
        ]
        """
        try:
            # Get all devices with client_id and connection data
            devices = Device.objects(client_id__ne=None, status=constants.OBJECT_STATUS_ACTIVE).only(
                'device_id', 'client_id', 'connection'
            )
            
            connected_devices = []
            
            for device in devices:
                connection = device.connection or {}
                status = connection.get('status', 'offline')
                last_seen = connection.get('last_seen', '')
                
                connected_devices.append({
                    "device_id": str(device.device_id),
                    "status": status,
                    "last_seen": last_seen
                })
            
            return response_utils.get_response_object(
                response_code=response_codes.CODE_SUCCESS,
                response_message=response_codes.MESSAGE_SUCCESS,
                response_data=connected_devices
            )
            
        except Exception as e:
            return response_utils.get_response_object(
                response_code=response_codes.CODE_OPERATION_FAILED,
                response_message=f"Failed to retrieve connected devices: {str(e)}",
                response_data=[]
            )
    