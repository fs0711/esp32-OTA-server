# Local imports
from esp32OTA.generic.models import Model
from esp32OTA.generic.services.utils import constants
from esp32OTA.generic.database import db


class APIToken(Model):
    access_token = db.StringField(required=True, unique=True)
    service_name = db.StringField(required=True)
    expiry_time = db.IntField(required=True)
    is_active = db.BooleanField(default=True)
    last_used = db.IntField(default=0)

    meta = {
        'collection': 'apitoken'
    }

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

    def display(self):
        return {
            "id": str(self.id),
            "access_token": self.access_token,
            "service_name": self.service_name,
            "expiry_time": self.expiry_time,
            "is_active": self.is_active,
            "last_used": self.last_used,
            "created_on": self.created_on
        }
