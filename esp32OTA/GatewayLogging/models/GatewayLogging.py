# Python imports

# Framework imports

# Local imports
from esp32OTA.generic import models
from esp32OTA.generic import db
from esp32OTA.generic.services.utils import constants, common_utils


class GatewayLogging(models.Model):
    @classmethod
    def validation_rules(cls):
        return {

        }


    @classmethod
    def update_validation_rules(cls): return {

    }

    payload = db.DictField(required=True)
    log_type = db.StringField(required=True) # "sent" or "received"

    def __str__(self):
        return str(self.pk)

    def display(self):
        return {
            constants.ID: str(self[constants.ID]),
            "payload": self.payload,
            "log_type": self.log_type
        }

    def display_min(self):
        return {
            constants.ID: str(self[constants.ID])
        }