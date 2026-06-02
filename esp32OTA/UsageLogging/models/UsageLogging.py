# Python imports

# Framework imports

# Local imports
from esp32OTA.generic import models
from esp32OTA.generic import db
from esp32OTA.generic.services.utils import constants


class UsageLogging(models.Model):
    @classmethod
    def validation_rules(cls):
        return {}

    @classmethod
    def update_validation_rules(cls):
        return {}

    device_id = db.StringField(required=True)
    timestamp = db.StringField(required=True)
    socket_id = db.IntField(required=True)
    session_id = db.StringField(required=True)
    consumption = db.FloatField(required=True)
    current = db.FloatField(required=True)
    voltage = db.IntField(required=True)
    duration = db.IntField(required=True)
    is_completed = db.IntField(required=True)

    def __str__(self):
        return str(self.pk)

    def display(self):
        return {
            constants.ID: str(self[constants.ID]),
            constants.USAGE_LOGGING__TIMESTAMP: self.timestamp,
            constants.USAGE_LOGGING__SOCKET_ID: self.socket_id,
            constants.USAGE_LOGGING__SESSION_ID: self.session_id,
            constants.USAGE_LOGGING__CONSUMPTION: self.consumption,
            constants.USAGE_LOGGING__CURRENT: self.current,
            constants.USAGE_LOGGING__VOLTAGE: self.voltage,
            constants.USAGE_LOGGING__DURATION: self.duration,
            constants.USAGE_LOGGING__IS_COMPLETED: self.is_completed
        }

    def display_min(self):
        return {
            constants.ID: str(self[constants.ID])
        }