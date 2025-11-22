# Python imports

# Framework imports

# Local imports
from esp32OTA.generic import models
from esp32OTA.generic import db
from esp32OTA.generic.services.utils import constants, common_utils


class DeviceType(models.Model):
    @classmethod
    def validation_rules(cls):
        return {
            constants.DEVICE_TYPE__DEVICE_TYPE: [{"rule": "required"}, {"rule": "datatype", "datatype": str}],
            constants.DEVICE_TYPE__TYPE_CODE: [{"rule": "required"},{"rule": "unique", "Model": cls,"Field": constants.DEVICE_TYPE__TYPE_CODE}, {"rule": "datatype", "datatype": str}],
            constants.DEVICE_TYPE__DESCRIPTION: [{"rule": "datatype", "datatype": str}],
            constants.DEVICE_TYPE__BILL_OF_MATERIAL: [{"rule": "datatype", "datatype": dict}],
        }

    @classmethod
    def update_validation_rules(cls):
        return {
            constants.DEVICE_TYPE__DEVICE_TYPE: [{"rule": "datatype", "datatype": str}],
            constants.DEVICE_TYPE__TYPE_CODE: [{"rule": "unique", "Model": cls,"Field": constants.DEVICE_TYPE__TYPE_CODE}, {"rule": "datatype", "datatype": str}],
            constants.DEVICE_TYPE__DESCRIPTION: [{"rule": "datatype", "datatype": str}],
            constants.DEVICE_TYPE__BILL_OF_MATERIAL: [{"rule": "datatype", "datatype": dict}],
        }

    device_type = db.StringField(required=True)
    type_code = db.StringField(required=True, unique=True)
    description = db.StringField()
    bom = db.DictField(default={})

    def __str__(self):
        return str(self.pk)

    def display(self):
        return {
            constants.ID: str(self[constants.ID]),
            constants.DEVICE_TYPE__DEVICE_TYPE: self[constants.DEVICE_TYPE__DEVICE_TYPE],
            constants.DEVICE_TYPE__TYPE_CODE: self[constants.DEVICE_TYPE__TYPE_CODE],
            constants.DEVICE_TYPE__DESCRIPTION: self[constants.DEVICE_TYPE__DESCRIPTION],
            constants.DEVICE_TYPE__BILL_OF_MATERIAL: self[constants.DEVICE_TYPE__BILL_OF_MATERIAL],
            constants.STATUS: self[constants.STATUS],
            constants.CREATED_BY: self[constants.CREATED_BY].fetch().name,
            constants.CREATED_ON: self[constants.CREATED_ON],
            constants.UPDATED_ON: self[constants.UPDATED_ON],
        }

    def display_min(self):
        return {
            constants.ID: str(self[constants.ID]),
            constants.DEVICE_TYPE__DEVICE_TYPE: self[constants.DEVICE_TYPE__DEVICE_TYPE],
            constants.DEVICE_TYPE__TYPE_CODE: self[constants.DEVICE_TYPE__TYPE_CODE],
            constants.CREATED_ON: self[constants.CREATED_ON],
        }
