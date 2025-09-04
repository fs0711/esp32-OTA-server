# Python imports

# Framework imports

# Local imports
from esp32OTA.generic import models
from esp32OTA.generic import db
from esp32OTA.generic.services.utils import constants, common_utils
from esp32OTA.IoManagement.models.Io import Io


class Io_data(models.Model):
    @classmethod
    def validation_rules(cls):
        return {
            constants.IO_DATA__DATA: [{"rule": "required"}],
            constants.IO_DATA__ID:  [{"rule": "datatype", "datatype": str}],
        }


    @classmethod
    def update_validation_rules(cls): return {

    }


    val_int = db.IntField()
    val_float = db.FloatField()
    val_str = db.StringField()
    val_bool = db.BooleanField()
    io_id = db.LazyReferenceField('Io', required=True)
    trigger = db.IntField(default=0)
    schedule = db.IntField(default=0)


    def __str__(self):
        return str(self.pk)

    def display(self):
        return {
            constants.ID: str(self[constants.ID]),
            constants.IO_DATA__ID: str(self[constants.IO_DATA__ID]),
            constants.IO_DATA__VAL_BOOL: self[constants.IO_DATA__VAL_BOOL] if self[constants.IO_DATA__VAL_BOOL] != None else "",
            constants.IO_DATA__VAL_INT: self[constants.IO_DATA__VAL_INT] if self[constants.IO_DATA__VAL_INT] != None else 0,
            constants.IO_DATA__VAL_STR: self[constants.IO_DATA__VAL_STR] if self[constants.IO_DATA__VAL_STR] != None else "",
            constants.IO_DATA__VAL_FLOAT: self[constants.IO_DATA__VAL_FLOAT] if self[constants.IO_DATA__VAL_FLOAT] != None else 0.0,
            constants.IO_DATA__TRIGGER: self[constants.IO_DATA__TRIGGER] if self[constants.IO_DATA__TRIGGER] != None else "",
            constants.CREATED_ON: common_utils.epoch_to_datetime(self[constants.CREATED_ON])
        }

    def display_min(self):
        return {
            constants.ID: str(self[constants.ID]),
            constants.IO_DATA__VAL_BOOL: self[constants.IO_DATA__VAL_BOOL] if self[constants.IO_DATA__VAL_BOOL] != None else "",
            constants.IO_DATA__VAL_INT: self[constants.IO_DATA__VAL_INT] if self[constants.IO_DATA__VAL_INT] != None else 0,
            constants.IO_DATA__VAL_STR: self[constants.IO_DATA__VAL_STR] if self[constants.IO_DATA__VAL_STR] != None else "",
            constants.IO_DATA__VAL_FLOAT: self[constants.IO_DATA__VAL_FLOAT] if self[constants.IO_DATA__VAL_FLOAT] != None else "",
            constants.IO_DATA__TRIGGER: self[constants.IO_DATA__TRIGGER] if self[constants.IO_DATA__TRIGGER] != None else "",
        }