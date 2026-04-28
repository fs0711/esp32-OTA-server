# Python imports
import hmac
import hashlib

# Framework imports

# Local imports
from esp32OTA.generic.controllers import Controller
from esp32OTA.DeviceManagement.models.Device import Device
from esp32OTA.generic.services.utils import constants, response_codes, response_utils


class MQTTAuthController(Controller):
    Model = Device

    @classmethod
    def authenticate_mqtt_controller(cls, data):
        """
        Authenticate MQTT client using HMAC token
        :param data: dict containing 'username' (device_id) and 'password' (HMAC token)
        :return: response object
        """
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return response_utils.get_response_object(
                response_code=response_codes.CODE_VALIDATION_FAILED,
                response_message="Username and password are required",
                response_data=[]
            )
        
        # Find device by device_id
        device_numeric_id = int(username.split('-')[1]) if '-' in str(username) else username
        device_obj = cls.db_read_single_record(
            read_filter={
                constants.DEVICE__ID: device_numeric_id,
                constants.STATUS: constants.OBJECT_STATUS_ACTIVE
            }
        )
        
        if not device_obj:
            return response_utils.get_response_object(
                response_code=response_codes.CODE_AUTHENTICATION_FAILED,
                response_message="Invalid device credentials",
                response_data=[]
            )
        
        # Get the device's access token (this will be the HMAC secret)
        secret_key = device_obj[constants.DEVICE__ACCESS_TOKEN]
        
        # Compute expected HMAC signature
        # The message being signed is the username (device_id)
        expected_signature = hmac.new(
            secret_key.encode('utf-8'),
            username.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # Compare the provided password with the expected HMAC signature
        # Using hmac.compare_digest for timing-attack resistance
        if hmac.compare_digest(password, expected_signature):
            return response_utils.get_response_object(
                response_code=response_codes.CODE_SUCCESS,
                response_message="Authentication successful",
                response_data={
                    constants.DEVICE__ID: device_obj[constants.DEVICE__ID],
                    constants.DEVICE__NAME: device_obj[constants.DEVICE__NAME],
                    "authenticated": True
                }
            )
        else:
            return response_utils.get_response_object(
                response_code=response_codes.CODE_AUTHENTICATION_FAILED,
                response_message="Invalid HMAC signature",
                response_data=[]
            )
    
    @classmethod
    def authenticate_mqtt_superuser_controller(cls, data):
        """
        Check if MQTT client is a superuser
        For this implementation, only admin users can be superusers
        :param data: dict containing 'username'
        :return: response object
        """
        username = data.get('username')
        
        if not username:
            return response_utils.get_response_object(
                response_code=response_codes.CODE_VALIDATION_FAILED,
                response_message="Username is required",
                response_data={"is_superuser": False}
            )
        
        # Devices are not superusers
        # This endpoint can be extended if needed for admin users
        return response_utils.get_response_object(
            response_code=response_codes.CODE_SUCCESS,
            response_message="Not a superuser",
            response_data={"is_superuser": False}
        )
    
    @classmethod
    def authorize_mqtt_acl_controller(cls, data):
        """
        Authorize MQTT client access to specific topics
        :param data: dict containing 'username', 'topic', 'acc' (access type: 1=sub, 2=pub)
        :return: response object
        """
        username = data.get('username')
        topic = data.get('topic')
        acc = data.get('acc')  # 1 = subscribe, 2 = publish
        
        if not username or not topic:
            return response_utils.get_response_object(
                response_code=response_codes.CODE_VALIDATION_FAILED,
                response_message="Username and topic are required",
                response_data={"authorized": False}
            )
        
        # Find device by device_id
        device_obj = cls.db_read_single_record(
            read_filter={
                constants.DEVICE__ID: username,
                constants.STATUS: constants.OBJECT_STATUS_ACTIVE
            }
        )
        
        if not device_obj:
            return response_utils.get_response_object(
                response_code=response_codes.CODE_AUTHENTICATION_FAILED,
                response_message="Device not found",
                response_data={"authorized": False}
            )
        
        # Basic ACL: Allow device to publish/subscribe to topics containing their device_id
        # You can customize this logic based on your requirements
        if username in topic:
            return response_utils.get_response_object(
                response_code=response_codes.CODE_SUCCESS,
                response_message="Access authorized",
                response_data={"authorized": True}
            )
        else:
            return response_utils.get_response_object(
                response_code=response_codes.CODE_AUTHORIZATION_FAILED,
                response_message="Access denied",
                response_data={"authorized": False}
            )
