# Local Imports
from abc import abstractmethod
from esp32OTA.generic.services.utils import (
    constants, common_utils, response_codes, response_utils)
from esp32OTA.generic.services.utils.validate_data import validate_data


class Controller:

    @property
    @abstractmethod
    def Model(self):
        pass

    @classmethod
    def cls_get_obj(cls, read_filter, collection=None,
                    deleted_records=constants.DEFAULT_READ_DELETED_RECORDS):
        if not collection:
            collection = cls.Model
        if not deleted_records:
            read_filter.update(
                {constants.STATUS: constants.OBJECT_STATUS_ACTIVE})
        obj = cls.db_read_single_record(read_filter=read_filter)
        if not obj:
            return False, response_utils.get_response_object(
                response_code=response_codes.CODE_RECORD_NOT_FOUND,
                response_message=response_codes.MESSAGE_NOT_FOUND_DATA.format(
                    collection.__name__, read_filter
                )
            )
        return True, obj

    @classmethod
    def cls_validate_data(cls, data, validation_rules=None, return_data=False,
                          update_mode=constants.UPDATE_MODE__FULL):
        if not validation_rules:
            validation_rules = cls.Model.validation_rules()
        if update_mode == constants.UPDATE_MODE__PARTIAL:
            validation_rules =\
                {key: validation_rules[key]
                 for key in validation_rules.keys() & data.keys()}
        return validate_data(
            raw_data=data, return_data=return_data,
            validation_rules=validation_rules)

    # Database Layer
    @classmethod
    def db_read_single_record(cls, read_filter, collection=None,
                              deleted_records=constants
                              .DEFAULT_READ_DELETED_RECORDS):
        """
        read and return single record
        :param collection:
        :param read_filter:
        :return:
        """
        if not collection:
            collection = cls.Model
        if not deleted_records:
            read_filter.update(
                {constants.STATUS: constants.OBJECT_STATUS_ACTIVE})
        return collection.objects(**read_filter).order_by('-id').first()

    @classmethod
    def db_read_records(cls, read_filter, collection=None,
                        deleted_records=constants
                        .DEFAULT_READ_DELETED_RECORDS):
        """
        read and return multiple records based on the read filter
        :param collection:
        :param read_filter:
        :return:
        """
        if not collection:
            collection = cls.Model
        if not deleted_records:
            read_filter.update(
                {constants.STATUS: constants.OBJECT_STATUS_ACTIVE})
        return collection.objects(**read_filter).order_by('-id')

    @classmethod
    def db_update_single_record(cls, read_filter, update_filter,
                                collection=None,
                                validation_rules=None,
                                update_mode=constants.UPDATE_MODE__FULL,
                                default_validation=constants
                                .DEFAULT_VALIDATION,
                                deleted_records=constants
                                .DEFAULT_READ_DELETED_RECORDS):
        """
        update records based on the read filter
        :param collection:
        :param read_filter:
        :param update_filter:
        :return:
        """
        if not collection:
            collection = cls.Model
        # Check if validation_rules are provided Explicitly
        if not validation_rules:
            validation_rules = collection.validation_rules()
            validation_rules.update(
                collection.update_validation_rules()
            )
        if not deleted_records:
            read_filter.update(
                {constants.STATUS: constants.OBJECT_STATUS_ACTIVE})

        if update_mode == constants.UPDATE_MODE__PARTIAL:
            validation_rules =\
                {key: validation_rules[key]
                 for key in validation_rules.keys() & update_filter.keys()}
        is_valid = True
        if default_validation and is_valid:
            is_valid, error_messages = validate_data(
                update_filter, validation_rules)
        if is_valid:
            update_filter.update(
                {constants.UPDATED_BY: common_utils.current_user(),
                  constants.UPDATED_ON: common_utils.get_time()})
            return True, "", collection.objects(**read_filter).modify(new=True, **update_filter)
        return False, error_messages, None

    @classmethod
    def db_update_records(cls, read_filter, update_filter, collection=None,
                          validation_rules=None,
                          update_mode=constants.UPDATE_MODE__FULL,
                          default_validation=constants.DEFAULT_VALIDATION,
                          deleted_records=constants
                          .DEFAULT_READ_DELETED_RECORDS):
        """
        update records based on the read filter
        :param collection:
        :param read_filter:
        :param update_filter:
        :return:
        """
        if not collection:
            collection = cls.Model
        if not validation_rules:
            validation_rules = collection.validation_rules()
            validation_rules.update(
                collection.update_validation_rules()
            )
        if not deleted_records:
            read_filter.update(
                {constants.STATUS: constants.OBJECT_STATUS_ACTIVE})

        if update_mode == constants.UPDATE_MODE__PARTIAL:
            validation_rules = \
                {key: validation_rules[key]
                 for key in validation_rules.keys() & update_filter.keys()}
        is_valid = True
        if default_validation and is_valid:
            is_valid, error_messages = validate_data(
                update_filter, validation_rules)
        if is_valid:
            update_filter.update(
                {constants.UPDATED_BY: common_utils.current_user(),
                 constants.UPDATED_ON: common_utils.get_time()})
            return True, "", collection.objects(**read_filter)\
                .update(multi=True, full_result=True, **update_filter)
        return False, error_messages, None

    @classmethod
    def db_insert_record(cls, data, collection=None, validation_rules=None,
                         default_validation=constants.DEFAULT_VALIDATION,
                         db_commit=True, user=True):
        """
        Create records in database with respect to collection
        :param collection:
        :param data:
        :return:
        """
        if not collection:
            collection = cls.Model
        if not validation_rules:
            validation_rules = collection.validation_rules()
        is_valid = True
        if default_validation:
            is_valid, error_messages = validate_data(
                data, validation_rules)
        if is_valid:
            if user:
                data.update({
                    constants.STATUS: constants.OBJECT_STATUS_ACTIVE,
                    constants.CREATED_BY: common_utils.current_user(),
                    constants.UPDATED_BY: common_utils.current_user(),
                    constants.CREATED_ON: common_utils.get_time(),
                    constants.UPDATED_ON: common_utils.get_time(),
                })
            if not user:
                data.update({
                    constants.STATUS: constants.OBJECT_STATUS_ACTIVE,
                    constants.CREATED_ON: common_utils.get_time(),
                    constants.UPDATED_ON: common_utils.get_time(),
                })
            obj = collection(**data)
            if db_commit:
                obj.save()
            return True, "", obj
        else:
            return False, error_messages, None

    @classmethod
    def db_insert_bulk_record(cls, data, collection=None,
                              validation_rules=None,
                              default_validation=constants.DEFAULT_VALIDATION,
                              db_commit=True):
        """
        Create records in database with respect to collection
        :param collection:
        :param data:
        :return:
        """
        "TODO How to handle Bulk validation"
        if not collection:
            collection = cls.Model
        if not validation_rules:
            validation_rules = collection.validation_rules()
        is_valid = True
        error_message_list = []
        obj_list = []
        if default_validation:
            for entry in data:
                is_valid, error_messages = validate_data(
                    entry, validation_rules)
                error_message_list.append(error_messages)
                if is_valid:
                    entry.update({
                        constants.STATUS: constants.OBJECT_STATUS_ACTIVE,
                        constants.CREATED_BY: common_utils.current_user(),
                        constants.UPDATED_BY: common_utils.current_user(),
                        constants.CREATED_ON: common_utils.get_time(),
                        constants.UPDATED_ON: common_utils.get_time(),
                    })
                    obj_list.append(collection(**entry))
        if is_valid:
            if db_commit:
                return True, "", collection.objects.insert(obj_list)
            return True, "", obj_list
        return False, error_message_list, None

    @classmethod
    def db_insert_file(cls, data, collection=None, validation_rules=None,
                         default_validation=constants.DEFAULT_VALIDATION,
                         db_commit=True):
        """
        Create file in database with respect to collection
        :param collection:
        :param data:
        :return:
        """
        if not collection:
            collection = cls.Model
        if not validation_rules:
            validation_rules = collection.validation_rules()
        is_valid = True
        if default_validation:
            is_valid, error_messages = validate_data(
                data, validation_rules)
        if is_valid:
            data.update({
                constants.STATUS: constants.OBJECT_STATUS_ACTIVE,
                constants.CREATED_BY: common_utils.current_user(),
                constants.UPDATED_BY: common_utils.current_user(),
                constants.CREATED_ON: common_utils.get_time(),
                constants.UPDATED_ON: common_utils.get_time(),
            })
            
            obj = collection(**data)
            if db_commit:
                obj.save()
            return True, "", obj
        else:
            return False, error_messages, None