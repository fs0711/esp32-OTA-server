# Python imports

# Framework imports

# Local imports
from esp32OTA.generic import models
from esp32OTA.generic import db
from esp32OTA.generic.services.utils import constants, common_utils
from esp32OTA.UserManagement.models.User import User


class Notification(models.Model):
    @classmethod
    def validation_rules(cls):
        return {
            
        }


    @classmethod
    def update_validation_rules(cls): return {
            
    }

    message = db.StringField(required=True)
    send = db.BooleanField(default=False)
    read = db.BooleanField(default=False)
    title = db.StringField(required=True)
    type = db.StringField(required=True)
    related_device = db.ReferenceField('Device', required=False)
    
    def __str__(self):
        return str(self.pk)

    def display(self):
        return {
            constants.ID: str(self[constants.ID]),
            constants.NOTIFICATION__MESSAGE: self[constants.NOTIFICATION__MESSAGE],
            constants.NOTIFICATION__SEND: self[constants.NOTIFICATION__SEND],
            constants.NOTIFICATION__READ: self[constants.NOTIFICATION__READ],
            constants.NOTIFICATION__TITLE: self[constants.NOTIFICATION__TITLE],
            constants.NOTIFICATION__TYPE: self[constants.NOTIFICATION__TYPE],
            constants.NOTIFICATION__RELATED_DEVICE: str(self[constants.NOTIFICATION__RELATED_DEVICE]) if self[constants.NOTIFICATION__RELATED_DEVICE] else None,
        }
