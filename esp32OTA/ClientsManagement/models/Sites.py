# Python imports

# Framework imports

# Local imports
from esp32OTA.generic import models
from esp32OTA.generic import db
from esp32OTA.generic.services.utils import constants, common_utils
from esp32OTA.ClientsManagement.models.Clients import Clients

class Sites(models.Model):
    @classmethod
    def validation_rules(cls):
        return {
            constants.SITE__NAME: [{"rule": "required"}, {"rule": "datatype", "datatype": str}],
            constants.SITE__CP_PHONE_NUMBER:  [{"rule": "datatype", "datatype": list}],
            constants.SITE__CP_EMAIL_ADDRESS: [{"rule": "email"}, {"rule": "datatype", "datatype": str}],
            constants.SITE__COUNTRY: [{"rule": "required"}, {"rule": "datatype", "datatype": str}],
            constants.SITE__CITY: [{"rule": "required"}, {"rule": "datatype", "datatype": str}],
            constants.SITE__ZIPCODE: [{"rule": "datatype", "datatype": str}],
            constants.SITE__CONTACT_PERSON: [{"rule": "datatype", "datatype": str}],
        }

    @classmethod
    def update_validation_rules(cls): return {

    }

    name = db.StringField(required=True)
    client = db.LazyReferenceField('Clients', required=True)
    contact_person = db.StringField(required=True)
    cp_phone_number = db.ListField()
    cp_email_address = db.StringField()
    address = db.StringField()
    country = db.StringField(required=True)
    city = db.StringField(required=True)
    zipcode = db.StringField(required=True)
    site_id = db.SequenceField(value_decorator='ST-{}'.format)

    def __str__(self):
        return str(self.pk)

    def display(self):
        return {
            constants.ID: str(self[constants.ID]),
            constants.SITE__ID: self[constants.SITE__ID],
            constants.SITE__NAME: self[constants.SITE__NAME],
            constants.SITE__CP_PHONE_NUMBER: self[constants.SITE__CP_PHONE_NUMBER],
            constants.SITE__CP_EMAIL_ADDRESS: self[constants.SITE__CP_EMAIL_ADDRESS],
            constants.SITE__COUNTRY: self[constants.SITE__COUNTRY],
            constants.SITE__CITY: self[constants.SITE__CITY],
            constants.SITE__CONTACT_PERSON: self[constants.SITE__CONTACT_PERSON],
            constants.STATUS: self[constants.STATUS],
            constants.CREATED_BY: self.created_by.fetch().name,
            constants.CREATED_ON: self[constants.CREATED_ON],
            constants.UPDATED_ON: self[constants.UPDATED_ON],
        }

    def display_min(self):
        return {
            constants.ID: str(self[constants.ID]),
            constants.SITE__ID: self[constants.SITE__ID],
            constants.SITE__NAME: self[constants.SITE__NAME],
            constants.CREATED_ON: common_utils.epoch_to_datetime(self[constants.CREATED_ON]),
        }