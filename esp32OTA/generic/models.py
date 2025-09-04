# Python Imports
from abc import abstractmethod
# Local Imports
from esp32OTA.generic import db
from esp32OTA.generic.services.utils import common_utils, constants


class Model(db.Document):
    meta = {'allow_inheritance': True, 'abstract': True}
    created_on = db.IntField(default=common_utils.get_time())
    updated_on = db.IntField(
        default=common_utils.get_time(), onupdate=common_utils.get_time())
    created_by = db.LazyReferenceField("User")
    updated_by = db.LazyReferenceField("User")
    status = db.DictField(default=constants.OBJECT_STATUS_ACTIVE)

    @abstractmethod
    def display(self):
        return {}


class EmbeddedModel(db.EmbeddedDocument):
    meta = {'allow_inheritance': True, 'abstract': True}
    created_on = db.IntField(default=common_utils.get_time())
    updated_on = db.IntField(
        default=common_utils.get_time(), onupdate=common_utils.get_time())
    created_by = db.ReferenceField("User")
    updated_by = db.ReferenceField("User")
    status = db.DictField(default=constants.OBJECT_STATUS_ACTIVE)

    @abstractmethod
    def display(self):
        return {}
