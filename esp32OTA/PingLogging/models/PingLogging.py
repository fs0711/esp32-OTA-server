# Python imports

# Framework imports

# Local imports
from esp32OTA.generic import models
from esp32OTA.generic import db
from esp32OTA.generic.services.utils import constants


class PingLogging(models.Model):
    @classmethod
    def validation_rules(cls):
        return {}

    @classmethod
    def update_validation_rules(cls):
        return {}

    device_id = db.StringField(required=True)
    socket_status = db.IntField(required=True)
    session_id = db.StringField(required=False, allow_null=True)
    box_open_request = db.BooleanField(required=True)
    credit = db.FloatField(required=True)

    def __str__(self):
        return str(self.pk)

    def display(self):
        return {
            constants.ID: str(self[constants.ID]),
            constants.PING_LOGGING__DEVICE_ID: self.device_id,
            constants.PING_LOGGING__SOCKET_STATUS: self.socket_status,
            constants.PING_LOGGING__SESSION_ID: self.session_id,
            constants.PING_LOGGING__BOX_OPEN_REQUEST: self.box_open_request,
            constants.PING_LOGGING__CREDIT: self.credit,
            constants.CREATED_ON: self.created_on,
            constants.UPDATED_ON: self.updated_on
        }

    def display_min(self):
        return {
            constants.ID: str(self[constants.ID])
        }
