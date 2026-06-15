# Python imports

# Framework imports

# Local imports
from esp32OTA.generic.controllers import Controller
from esp32OTA.PingLogging.models.PingLogging import PingLogging
from esp32OTA.generic.services.utils import constants, response_codes, response_utils


class PingLoggingController(Controller):
    Model = PingLogging  # type: ignore[assignment]

    @classmethod
    def log_ping(cls, data):
        """
        Logs ping data by mapping payload fields to Model fields.
        """
        _, _, obj = cls.db_insert_file(
            data=data, default_validation=True)
        
        return obj

    @classmethod
    def update_ping(cls, log_id, data):
        """
        Updates an existing ping log entry.
        """
        success, message, obj = cls.db_update_single_record(
            read_filter={constants.ID: log_id},
            update_filter=data,
            update_mode=constants.UPDATE_MODE__PARTIAL
        )
        return obj

    @classmethod
    def read_controller(cls):
        return response_utils.get_response_object(
            response_code=response_codes.CODE_SUCCESS,
            response_message=response_codes.MESSAGE_SUCCESS,
            response_data=[
                obj.display() for obj in cls.db_read_records(read_filter={}, deleted_records=True)
            ]
        )
