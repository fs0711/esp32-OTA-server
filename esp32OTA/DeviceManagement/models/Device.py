# Python imports

# Framework imports

# Local imports
from esp32OTA.generic import models
from esp32OTA.generic import db
from esp32OTA.generic.services.utils import constants, common_utils
from esp32OTA.UserManagement.models.User import User


class Device(models.Model):
    @classmethod
    def validation_rules(cls):
        return {
            constants.DEVICE__NAME: [{"rule": "required"}, {"rule": "datatype", "datatype": str}],
        }


    @classmethod
    def update_validation_rules(cls): return {
            constants.DEVICE__NAME: [{"rule": "datatype", "datatype": str}],
    }


    name = db.StringField(required=True)
    device_type = db.LazyReferenceField(document_type='DeviceType')
    variables = db.DictField(default={})
    device_id = db.SequenceField(value_decorator='DV-{}'.format)
    access_token = db.StringField(required=True)
    serial_number = db.StringField()
    last_updated = db.IntField(default=0)
    hw_version = db.StringField(default="")
    fw_version = db.StringField(default="")
    new_fw_version = db.StringField(default="")
    rollback = db.BooleanField(default=False)
    update_config = db.BooleanField(default=False)
    update_path= db.StringField(default="")
    fw_file = db.LazyReferenceField(document_type='Firmware')
    qr_code = db.StringField(default="")
    connection = db.DictField(default={})

    def __str__(self):
        return str(self.pk)

    def display(self):
        return {
            constants.ID: str(self[constants.ID]),
            constants.DEVICE__ID: self[constants.DEVICE__ID],
            constants.DEVICE__NAME: self[constants.DEVICE__NAME],
            constants.DEVICE__TYPE: self[constants.DEVICE__TYPE].fetch().device_type,
            constants.DEVICE__VARIABLES: self[constants.DEVICE__VARIABLES],
            constants.DEVICE__ACCESS_TOKEN: self[constants.DEVICE__ACCESS_TOKEN],
            constants.STATUS: self[constants.STATUS],
            constants.CREATED_BY: self[constants.CREATED_BY].fetch().name,
            constants.CREATED_ON: self[constants.CREATED_ON],
            constants.UPDATED_ON: self[constants.UPDATED_ON],
            constants.DEVICE__HARDWARE_VERSION: self[constants.DEVICE__HARDWARE_VERSION],
            constants.DEVICE__FIRMWARE_VERSION: self[constants.DEVICE__FIRMWARE_VERSION],
            constants.DEVICE__NEW_FIRMWARE_VERSION: self[constants.DEVICE__NEW_FIRMWARE_VERSION],
            constants.DEVICE__ROLLBACK: self[constants.DEVICE__ROLLBACK],
            constants.DEVICE__UPDATE_CONFIG: self[constants.DEVICE__UPDATE_CONFIG],
            constants.DEVICE__UPDATE_PATH: self[constants.DEVICE__UPDATE_PATH],
            constants.DEVICE__FIRMWARE_FILE: str(self[constants.DEVICE__FIRMWARE_FILE].fetch().file_name) if self[constants.DEVICE__FIRMWARE_FILE] else "",
            constants.DEVICE__QR_CODE: self[constants.DEVICE__QR_CODE],
            constants.DEVICE__CONNECTION: self[constants.DEVICE__CONNECTION],
            constants.DEVICE__SERIAL_NUMBER: self[constants.DEVICE__SERIAL_NUMBER]
        }

    def display_min(self):
        return {
            constants.ID: str(self[constants.ID]),
            constants.DEVICE__ID: self[constants.DEVICE__ID],
            constants.DEVICE__NAME: self[constants.DEVICE__NAME],
            constants.CREATED_ON: self[constants.CREATED_ON],
            constants.DEVICE__ACCESS_TOKEN: self[constants.DEVICE__ACCESS_TOKEN],
            constants.DEVICE__TYPE: self[constants.DEVICE__TYPE].fetch().device_type,
            constants.DEVICE__CONNECTION: self[constants.DEVICE__CONNECTION],
            constants.DEVICE__SERIAL_NUMBER: self[constants.DEVICE__SERIAL_NUMBER]
        }
    
    def display_config(self):
        return {
            constants.DEVICE__HARDWARE_VERSION: self[constants.DEVICE__HARDWARE_VERSION],
            constants.DEVICE__FIRMWARE_VERSION: self[constants.DEVICE__FIRMWARE_VERSION],
            constants.DEVICE__NEW_FIRMWARE_VERSION: self[constants.DEVICE__NEW_FIRMWARE_VERSION],
            constants.DEVICE__ROLLBACK: self[constants.DEVICE__ROLLBACK],
            constants.DEVICE__UPDATE_CONFIG: self[constants.DEVICE__UPDATE_CONFIG],
            constants.DEVICE__UPDATE_PATH: self[constants.DEVICE__UPDATE_PATH],
            constants.DEVICE__FIRMWARE_FILE: str(self[constants.DEVICE__FIRMWARE_FILE].fetch().id) if self[constants.DEVICE__FIRMWARE_FILE] else "",
            constants.DEVICE__QR_CODE: self[constants.DEVICE__QR_CODE],
            constants.DEVICE__VARIABLES: self[constants.DEVICE__VARIABLES],
        }