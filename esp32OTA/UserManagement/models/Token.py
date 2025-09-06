# Python imports

# Local imports
from esp32OTA.generic import models, db
from esp32OTA.generic.services.utils import constants
from esp32OTA.UserManagement.models.User import User


class Token(models.Model):
    @classmethod
    def validation_rules(self):
        return {
            constants.TOKEN__ACCESS_TOKEN: [
                {"rule": "required"},
                {"rule": "unique",
                 "Model": self,
                 "Field": constants.TOKEN__ACCESS_TOKEN}],
            # constants.TOKEN__USER: [
            #     {"rule": "required"},
            #     {"rule": "exists",
            #      "Model": User,
            #      "Field": constants.ID}],
            constants.TOKEN__PLATFORM: [
                {"rule": "required"},
                {"rule": "choices",
                 "options": [constants.PLATFORM_WEB,
                             constants.PLATFORM_MOBILE,
                             constants.PLATFORM_EMAIL,
                             constants.PLATFORM_DEVICE]}],
            constants.TOKEN__PURPOSE: [
                {"rule": "required"},
                {"rule": "choices",
                 "options": [constants.PURPOSE_LOGIN,
                             constants.PURPOSE_RESET_PASSWORD,
                             constants.PURPOSE_IOT]}],
            constants.TOKEN__EXPIRY_TIME: [{"rule": "required"}],
            constants.TOKEN__IS_EXPIRED: [],
            constants.TOKEN__IS_REVOKED: [],
        }

    @ classmethod
    def update_validation_rules(self): return{
    }

    access_token = db.StringField(required=True, unique=True)
    user = db.LazyReferenceField(document_type= "User")
    purpose = db.StringField(required=True)
    expiry_time = db.IntField(required=True)
    is_expired = db.BooleanField(default=False)
    is_revoked = db.BooleanField(default=False)
    platform = db.StringField(required=True)

    def display(self):
        return {
            constants.TOKEN__ACCESS_TOKEN: self.access_token,
            constants.TOKEN__USER: self.user.fetch().display() if self.user else '',
            constants.TOKEN__PURPOSE: self.purpose,
            constants.TOKEN__EXPIRY_TIME: self.expiry_time,
            constants.TOKEN__IS_EXPIRED: self.is_expired,
            constants.TOKEN__IS_REVOKED: self.is_revoked,
            constants.STATUS: self.status,
            constants.TOKEN__PLATFORM: self.platform
        }
