# Python imports

# Framework imports

# Local imports
from esp32OTA.generic import models
from esp32OTA.generic import db
from esp32OTA.generic.services.utils import constants, common_utils


class Firmware(models.Model):
    @classmethod
    def validation_rules(cls):
        return {
            constants.FIRMWARE__DEVICE_TYPE: [{"rule": "required"}, {"rule": "choices", "options": constants.DEVICE__TYPE_LIST}],
            constants.FIRMWARE__VERSION:  [{"rule": "required"}, {"rule": "datatype", "datatype": str}],
            constants.FIRMWARE__FILE: [{"rule": "required"}],
            constants.FIRMWARE__DESCRIPTION: [{"rule": "datatype", "datatype": str}],
            constants.FIRMWARE__HARDWARE_VERSION: [{"rule": "datatype", "datatype": str}],
            constants.FIRMWARE__UPDATE_PATH: [{"rule": "choices", "options": constants.FIRMWARE__UPDATE_PATH_LIST}]
        }


    @classmethod
    def update_validation_rules(cls): return {    
        
    }


    version = db.StringField(required=True)
    device_type = db.StringField(required=True)
    file = db.FileField(required=True)
    checksum = db.StringField(required=True)
    file_name = db.StringField()
    description = db.StringField()
    hw_version = db.StringField()
    update_path = db.StringField()
    released_on = db.IntField()

    def __str__(self):
        return str(self.pk)

    def display(self):
        return {
            constants.ID: str(self[constants.ID]),
            constants.STATUS: self[constants.STATUS],
            constants.CREATED_BY: self.created_by.fetch().name,
            constants.CREATED_ON: self[constants.CREATED_ON],
            constants.UPDATED_ON: self[constants.UPDATED_ON],
            constants.FIRMWARE__VERSION: self[constants.FIRMWARE__VERSION],
            constants.FIRMWARE__DEVICE_TYPE: self[constants.FIRMWARE__DEVICE_TYPE],
            constants.FIRMWARE__FILE: self[constants.FIRMWARE__FILE],
            constants.FIRMWARE__CHECKSUM: self[constants.FIRMWARE__CHECKSUM],
            constants.FIRMWARE__DESCRIPTION: self[constants.FIRMWARE__DESCRIPTION],
            constants.FIRMWARE__HARDWARE_VERSION: self[constants.FIRMWARE__HARDWARE_VERSION],
            constants.FIRMWARE__UPDATE_PATH: self[constants.FIRMWARE__UPDATE_PATH],
            constants.FIRMWARE__RELEASED_ON: self[constants.FIRMWARE__RELEASED_ON]
        }

    def display_min(self):
        return {
            constants.ID: str(self[constants.ID]),
            constants.DEVICE__ID: self[constants.DEVICE__ID],
            constants.DEVICE__NAME: self[constants.DEVICE__NAME],
            constants.CREATED_ON: self[constants.CREATED_ON],
        }