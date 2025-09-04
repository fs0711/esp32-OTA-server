# Python imports

# Framework imports

# Local imports
from esp32OTA.generic import models
from esp32OTA.generic import db
from esp32OTA.DeviceManagement.models.Device import Device
from esp32OTA.generic.services.utils import constants, common_utils


class Io(models.Model):
    @classmethod
    def validation_rules(cls):
        return {
            constants.IO__NAME: [{"rule": "required"}, {"rule": "datatype", "datatype": str}],
            constants.IO__TYPE:  [{"rule": "required"}, {"rule": "choices", "options": constants.IO__TYPE_LIST}],
            constants.IO__DEVICE: [{"rule": "required"}, {"rule": "datatype", "datatype": str}],
            constants.IO__DATA_TYPE: [{"rule": "required"}, {"rule": "choices", "options": constants.IO__DATA_TYPE_LIST}],
            constants.IO__UNIT: [{"rule": "datatype", "datatype": str}],
        }


    @classmethod
    def update_validation_rules(cls): return {

    }


    name = db.StringField(required=True)
    type = db.StringField(required=True)
    data_type = db.StringField(required=True)
    unit = db.StringField(required=True, default="")
    device = db.LazyReferenceField('Device', required=True)
    io_id = db.SequenceField(value_decorator='IO-{}'.format)
    display_type = db.ListField(default=[])


    def __str__(self):
        return str(self.pk)

    def display(self):
        return {
            constants.ID: str(self[constants.ID]),
            constants.IO__ID: self[constants.IO__ID],
            constants.IO__NAME: self[constants.IO__NAME],
            constants.IO__DATA_TYPE: self[constants.IO__DATA_TYPE],
            constants.IO__DEVICE: self[constants.IO__DEVICE].fetch().display(),
            constants.IO__TYPE: self[constants.IO__TYPE],
            constants.IO__UNIT: self[constants.IO__UNIT],
            constants.IO__DISPLAY: self[constants.IO__DISPLAY] if self[constants.IO__DISPLAY] else [],
            constants.CREATED_ON: self[constants.CREATED_ON],
            constants.UPDATED_ON: self[constants.UPDATED_ON],
        }
    
    def display_types(self):
        return {
            constants.IO__DATA_TYPE: self[constants.IO__DATA_TYPE],
            constants.IO__UNIT: self[constants.IO__UNIT],
        }