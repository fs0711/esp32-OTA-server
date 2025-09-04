# Python imports

# Framework imports

# Local imports
from esp32OTA.generic import models
from esp32OTA.generic import db
from esp32OTA.generic.services.utils import constants, common_utils
from esp32OTA.config import config



class Organization(models.Model):
    @classmethod
    def validation_rules(cls):
        return{
            constants.ORGANIZTION__NAME:[{'rule':'required'}, {'rule':'datatype', 'datatype':str}],
            constants.ORGANIZATION__ADDRESS:[{'rule':'required'}, {'rule':'datatype', 'datatype':str}],
            constants.ORGANIZATION__CITY:[{'rule':'required'}, {'rule':'datatype', 'datatype':str}],
            constants.ORGANIZATION__COUNTRY:[{'rule':'required'}, {'rule':'datatype', 'datatype':str}],
            constants.ORGANIZATION__CP_NAME:[{'rule':'required'}, {'rule':'datatype', 'datatype':str}],
            constants.ORGANIZATION__CP_EMAIL:[{'rule':'required'}, {'rule':'datatype', 'datatype':str}],
            constants.ORGANIZATION__CP_PHONE_NUMBER:[{'rule':'required'}, {'rule':'datatype', 'datatype':list}],
            constants.ORGANIZATION__NTN:[{'rule':'datatype', 'datatype': str}],
            constants.ORGANIZATION__CUSTOM_FIELDS:[{'rule':'datatype', 'datatype': dict}]
        }
    
    @classmethod
    def update_validation_rules(cls): return {
    }

    name = db.StringField(required=True)
    address = db.StringField(required=True)
    city = db.StringField(required=True)
    country = db.StringField(required=True)
    cp_name = db.StringField(required=True)
    cp_email_address = db.StringField(required=True)
    cp_phone_number = db.ListField(required=True)
    ntn = db.StringField(default='')
    custom_fields = db.DictField(default={})


    def __str__(self):
        return str(self.pk)

            # constants.CALL_RECORD__DATE: self[constants.CALL_RECORD__DATE],


    def display(self):
        return {
            constants.ID:str(self[constants.ID]),
            constants.ORGANIZATION__NAME: self[constants.ORGANIZATION__NAME],
            constants.ORGANIZATION__ADDRESS: self[constants.ORGANIZATION__ADDRESS],
            constants.ORGANIZATION__CITY: self[constants.ORGANIZATION__CITY],
            constants.ORGANIZATION__COUNTRY: self[constants.ORGANIZATION__COUNTRY],
            constants.ORGANIZATION__CP_NAME: self[constants.ORGANIZATION__CP_NAME],
            constants.ORGANIZATION__CP_EMAIL: self[constants.ORGANIZATION__CP_EMAIL],
            constants.ORGANIZATION__CP_PHONE_NUMBER: self[constants.ORGANIZATION__CP_PHONE_NUMBER],
            constants.ORGANIZATION__NTN: self[constants.ORGANIZATION__NTN],
            constants.ORGANIZATION__CUSTOM_FIELDS: self[constants.ORGANIZATION__CUSTOM_FIELDS] if constants.ORGANIZATION__CUSTOM_FIELDS else {}
        }

    def dispaly_id_name(self):
        return{
            constants.ID:str(self[constants.ID]),
            constants.ORGANIZATION__NAME: self[constants.ORGANIZATION__NAME]
        }



