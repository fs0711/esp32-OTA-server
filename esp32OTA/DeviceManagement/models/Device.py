# Python imports

# Framework imports

# Local imports
from esp32OTA.generic import models
from esp32OTA.generic import db
from esp32OTA.OrganizationsManagement.models.Organization import Organization
from esp32OTA.ClientsManagement.models.Clients import Clients
from esp32OTA.ClientsManagement.models.Sites import Sites
from esp32OTA.generic.services.utils import constants, common_utils
from esp32OTA.UserManagement.models.User import User


class Device(models.Model):
    @classmethod
    def validation_rules(cls):
        return {
            constants.DEVICE__NAME: [{"rule": "required"}, {"rule": "datatype", "datatype": str}],
            constants.DEVICE__TYPE:  [{"rule": "required"}, {"rule": "choices", "options": constants.DEVICE__TYPE_LIST}],
            constants.DEVICE__CLIENT: [{"rule": "required"}, {"rule": "datatype", "datatype": str}],
            constants.DEVICE__SITE: [{"rule": "required"}, {"rule": "datatype", "datatype": str}],
            constants.DEVICE__ORGANIZATION: [{"rule": "required"}, {"rule": "datatype", "datatype": str}]
        }


    @classmethod
    def update_validation_rules(cls): return {
            constants.DEVICE__NAME: [{"rule": "datatype", "datatype": str}],
            constants.DEVICE__TYPE:  [{"rule": "choices", "options": constants.DEVICE__TYPE_LIST}],
            constants.DEVICE__CLIENT: [{"rule": "datatype", "datatype": str}],
            constants.DEVICE__SITE: [{"rule": "datatype", "datatype": str}],
            constants.DEVICE__ORGANIZATION: [{"rule": "datatype", "datatype": str}]
    }


    name = db.StringField(required=True)
    type = db.StringField(required=True)
    variables = db.ListField(default=[])
    inputs = db.ListField(default=[])
    outputs = db.ListField(default=[])
    client = db.LazyReferenceField(Clients, required=True)
    site = db.LazyReferenceField(Sites, required=True)
    organization = db.LazyReferenceField(Organization, required=True)
    device_id = db.SequenceField(value_decorator='DV-{}'.format)
    access_token = db.StringField(required=True)


    def __str__(self):
        return str(self.pk)

    def display(self):
        return {
            constants.ID: str(self[constants.ID]),
            constants.DEVICE__ID: self[constants.DEVICE__ID],
            constants.DEVICE__NAME: self[constants.DEVICE__NAME],
            constants.DEVICE__TYPE: self[constants.DEVICE__TYPE],
            constants.DEVICE__VARIABLES: self[constants.DEVICE__VARIABLES],
            constants.DEVICE__INPUTS: self[constants.DEVICE__INPUTS],
            constants.DEVICE__OUTPUTS: self[constants.DEVICE__OUTPUTS],
            constants.DEVICE__ORGANIZATION: self[constants.DEVICE__ORGANIZATION].fetch().name,
            constants.DEVICE__CLIENT: self[constants.DEVICE__CLIENT].fetch().name,
            constants.DEVICE__SITE: self[constants.DEVICE__SITE].fetch().name,
            constants.DEVICE__ACCESS_TOKEN: self[constants.DEVICE__ACCESS_TOKEN],
            constants.STATUS: self[constants.STATUS],
            constants.CREATED_BY: self.created_by.fetch().name,
            constants.CREATED_ON: self[constants.CREATED_ON],
            constants.UPDATED_ON: self[constants.UPDATED_ON],
        }

    def display_min(self):
        return {
            constants.ID: str(self[constants.ID]),
            constants.DEVICE__ID: self[constants.DEVICE__ID],
            constants.DEVICE__NAME: self[constants.DEVICE__NAME],
            constants.CREATED_ON: self[constants.CREATED_ON],
        }