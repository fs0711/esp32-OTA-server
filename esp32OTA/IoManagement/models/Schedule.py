# Python imports

# Framework imports

# Local imports
from esp32OTA.generic import models
from esp32OTA.generic import db
from esp32OTA.generic.services.utils import constants, common_utils
from esp32OTA.IoManagement.models.Io import Io


class Schedule(models.Model):
    @classmethod
    def validation_rules(cls):
        return {
            constants.SCHEDULE__START_TIME: [{"rule": "required", "datatype": int}],
            constants.SCHEDULE__DURATION: [{"rule": "required", "datatype": int}],
            constants.SCHEDULE__DAY: [{"rule": "required", "datatype": int}],
            constants.SCHEDULE__IO_ID:  [{"rule": "datatype", "datatype": str}]
        }


    @classmethod
    def update_validation_rules(cls): return {

    }

    day = db.IntField()
    start_time = db.IntField()
    end_time = db.IntField()
    duration = db.IntField()
    io_id = db.LazyReferenceField('Io', required=True)


    def __str__(self):
        return str(self.pk)

    def display(self):
        return {
            constants.ID: str(self[constants.ID]),
            constants.SCHEDULE__DAY: self[constants.SCHEDULE__DAY],
            constants.SCHEDULE__START_TIME: self[constants.SCHEDULE__START_TIME],
            constants.SCHEDULE__DURATION: self[constants.SCHEDULE__DURATION],
            constants.SCHEDULE__IO_ID: str(self[constants.SCHEDULE__IO_ID].fetch().id),
            constants.CREATED_ON: common_utils.epoch_to_datetime(self[constants.CREATED_ON])
        }