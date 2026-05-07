# Python imports

# Local imports
from esp32OTA.generic import models, db
from esp32OTA.generic.services.utils import constants


class Token(models.Model):
    @classmethod
    def validation_rules(self):
        return {
            constants.TOKEN__ACCESS_TOKEN: [
                {"rule": "required"},
                {"rule": "unique",
                 "Model": self,
                 "Field": constants.TOKEN__ACCESS_TOKEN}],
            constants.TOKEN__SERVICE_NAME: [
                {"rule": "required"}
            ],
            constants.TOKEN__EXPIRY_TIME: [{"rule": "required"}],
        }

    @classmethod
    def update_validation_rules(self):
        return {}

    access_token = db.StringField(required=True, unique=True)
    service_name = db.StringField(required=True)
    expiry_time = db.IntField(required=True)
    is_active = db.BooleanField(default=True)

    def display(self):
        return {
            "id": str(self.id),
            "access_token": self.access_token,
            "service_name": self.service_name,
            "expiry_time": self.expiry_time,
            "is_active": self.is_active,
            "created_on": self.created_on
        }

