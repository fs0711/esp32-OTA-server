# Python imports

# Framework imports
from flask import Response

# Local imports
from esp32OTA.generic.controllers import Controller
from esp32OTA.UsageLogging.models.UsageLogging import UsageLogging
from esp32OTA.generic.services.utils import constants, response_codes, response_utils


class UsageLoggingController(Controller):
    Model = UsageLogging  # type: ignore[assignment]

    @classmethod
    def log_usage(cls, data):
        """
        Logs usage data by mapping payload fields to Model fields.
        """
        _, _, obj = cls.db_insert_file(
            data=data, default_validation=True)
        
        return obj

    @classmethod
    def update_usage(cls, log_id, data):
        """
        Updates an existing usage log entry.
        """
        success, message, obj = cls.db_update_single_record(
            read_filter={constants.ID: log_id},
            update_filter=data,
            update_mode=constants.UPDATE_MODE__PARTIAL
        )
        return obj
