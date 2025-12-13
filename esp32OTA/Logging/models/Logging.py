# Python imports

# Framework imports

# Local imports
from esp32OTA.generic import models
from esp32OTA.generic import db
from esp32OTA.generic.services.utils import constants, common_utils


class Logging(models.Model):
    @classmethod
    def validation_rules(cls):
        return {

        }


    @classmethod
    def update_validation_rules(cls): return {

    }

    payload = db.StringField(required=True)

    def __str__(self):
        return str(self.pk)

    def display(self):
        return {
            constants.ID: str(self[constants.ID])
        }

    def display_min(self):
        return {
            constants.ID: str(self[constants.ID])
        }