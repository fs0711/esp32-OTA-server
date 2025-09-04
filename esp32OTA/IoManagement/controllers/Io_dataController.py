# Python imports
# Framework imports

# Local imports
from ast import Constant
from esp32OTA.generic.controllers import Controller
from esp32OTA.IoManagement.models.Io_data import Io_data
from esp32OTA.IoManagement.controllers.IoController import IoController
from esp32OTA.IoManagement.controllers.ScheduleController import ScheduleController
from esp32OTA.generic.services.utils import constants, response_codes, response_utils, common_utils, pipeline


class Io_dataController(Controller):
    Model = Io_data

    @classmethod
    def create_controller(cls, data):
        is_valid, error_messages = cls.cls_validate_data(data=data)
        if not is_valid:
            return response_utils.get_response_object(
                response_code=response_codes.CODE_VALIDATION_FAILED,
                response_message=response_codes.MESSAGE_VALIDATION_FAILED,
                response_data=error_messages
            )
        if is_valid:
            filter = {}
            if data.get(constants.ID):
                filter = {constants.ID:data[constants.ID]}
            if data.get(constants.IO_DATA__ID):
                data[constants.IO_DATA__ID] = data[constants.IO_DATA__ID][3:]
                filter = {constants.IO_DATA__ID:data[constants.IO_DATA__ID]}
            io = IoController.db_read_single_record(read_filter=filter)
            data[constants.IO_DATA__ID] = io
            if io[constants.IO__TYPE] == constants.IO__TYPE_LIST[0]:
                if io[constants.IO__DATA_TYPE] == constants.IO__DATA_TYPE_LIST[0]:
                    data[constants.IO_DATA__VAL_INT] = data[constants.IO_DATA__DATA]
                if io[constants.IO__DATA_TYPE] == constants.IO__DATA_TYPE_LIST[1]:
                    data[constants.IO_DATA__VAL_STR] = data[constants.IO_DATA__DATA]
                if io[constants.IO__DATA_TYPE] == constants.IO__DATA_TYPE_LIST[2]:
                    data[constants.IO_DATA__VAL_FLOAT] = data[constants.IO_DATA__DATA]
                if io[constants.IO__DATA_TYPE] == constants.IO__DATA_TYPE_LIST[3]:
                    data[constants.IO_DATA__VAL_BOOL] = data[constants.IO_DATA__DATA]
                del data[constants.IO_DATA__DATA]
            if io[constants.IO__TYPE] == constants.IO__TYPE_LIST[1]:
                io_data = cls.db_read_single_record(read_filter={constants.IO_DATA__ID:str(io[constants.ID])})
                if io_data:
                    data[constants.IO_DATA__TRIGGER] = io_data[constants.IO_DATA__TRIGGER]
                if io[constants.IO__DATA_TYPE] == constants.IO__DATA_TYPE_LIST[0]:
                    data[constants.IO_DATA__VAL_INT] = data[constants.IO_DATA__DATA]
                if io[constants.IO__DATA_TYPE] == constants.IO__DATA_TYPE_LIST[3]:
                    data[constants.IO_DATA__VAL_BOOL] = data[constants.IO_DATA__DATA]
                    if data[constants.IO_DATA__DATA] == 0:
                        data[constants.IO_DATA__TRIGGER] = 0
                del data[constants.IO_DATA__DATA]
            if io[constants.IO__TYPE] == constants.IO__TYPE_LIST[2]:
                if io[constants.IO__DATA_TYPE] == constants.IO__DATA_TYPE_LIST[0]:
                    data[constants.IO_DATA__VAL_INT] = data[constants.IO_DATA__DATA]
                if io[constants.IO__DATA_TYPE] == constants.IO__DATA_TYPE_LIST[1]:
                    data[constants.IO_DATA__VAL_STR] = data[constants.IO_DATA__DATA]
                if io[constants.IO__DATA_TYPE] == constants.IO__DATA_TYPE_LIST[2]:
                    data[constants.IO_DATA__VAL_FLOAT] = data[constants.IO_DATA__DATA]
                if io[constants.IO__DATA_TYPE] == constants.IO__DATA_TYPE_LIST[3]:
                    data[constants.IO_DATA__VAL_BOOL] = data[constants.IO_DATA__DATA]
                del data[constants.IO_DATA__DATA]
            _,_,obj = cls.db_insert_record(data=data, default_validation=False)
            return response_utils.get_response_object(
                response_code=response_codes.CODE_SUCCESS,
                response_message=response_codes.MESSAGE_SUCCESS,
                response_data=obj.display_min()
            )
        return response_utils.get_response_object(
            response_code=response_codes.CODE_CREATE_FAILED,
            response_message=response_codes.MESSAGE_OPERATION_FAILED
        )

    @classmethod
    def status_controller(cls, data):
        data[constants.IO_DATA__ID] = data[constants.IO_DATA__ID][3:]
        io = IoController.db_read_single_record(read_filter={constants.IO_DATA__ID:data[constants.IO_DATA__ID]})
        data[constants.IO_DATA__ID] = str(io[constants.ID])
        day = common_utils.get_day()
        time = common_utils.get_time_iso()
        schedules = ScheduleController.db_read_records(read_filter={constants.SCHEDULE__IO_ID:str(io[constants.ID]), constants.SCHEDULE__DAY:day})
        duration = 0
        for schedule in schedules:
            if time >= schedule[constants.SCHEDULE__START_TIME] and time <= (schedule[constants.SCHEDULE__START_TIME] + schedule[constants.SCHEDULE__DURATION]):
                duration = schedule[constants.SCHEDULE__DURATION]
                obj = cls.db_read_single_record(read_filter={constants.IO_DATA__ID:str(io[constants.ID]), constants.IO_DATA__SCHEDULE:1})
                if obj:
                    if obj[constants.CREATED_ON] >= common_utils.get_time() - ((duration + 1) * 60 * 1000):
                        obj = cls.db_read_single_record(read_filter={constants.IO_DATA__ID:str(io[constants.ID])})
                        return response_utils.get_response_object(
                            response_code=response_codes.CODE_SUCCESS,
                            response_message=response_codes.MESSAGE_SUCCESS,
                            response_data=obj.display_min()
                        )
                    else:
                        data_new = {
                        constants.IO_DATA__ID: str(io[constants.ID]),
                        constants.IO_DATA__VAL_BOOL: 0,
                        constants.IO_DATA__TRIGGER: 1,
                        constants.IO_DATA__SCHEDULE: 1
                        }
                        _,_,obj = cls.db_insert_record(data=data_new, default_validation=False)
                        return response_utils.get_response_object(
                            response_code=response_codes.CODE_SUCCESS,
                            response_message=response_codes.MESSAGE_SUCCESS,
                            response_data={"trigger": obj["trigger"]}
                        )
                else:
                    data_new = {
                    constants.IO_DATA__ID: str(io[constants.ID]),
                    constants.IO_DATA__VAL_BOOL: 0,
                    constants.IO_DATA__TRIGGER: 1,
                    constants.IO_DATA__SCHEDULE: 1
                    }
                    _,_,obj = cls.db_insert_record(data=data_new, default_validation=False)
                    return response_utils.get_response_object(
                        response_code=response_codes.CODE_SUCCESS,
                        response_message=response_codes.MESSAGE_SUCCESS,
                        response_data={"trigger": obj["trigger"]}
                    )
        obj = cls.db_read_single_record(read_filter={constants.IO_DATA__ID:str(io[constants.ID])})
        return response_utils.get_response_object(
            response_code=response_codes.CODE_SUCCESS,
            response_message=response_codes.MESSAGE_SUCCESS,
            response_data=obj.display_min()
        )

    @classmethod
    def read_controller(cls, data):
        return response_utils.get_response_object(
            response_code=response_codes.CODE_SUCCESS,
            response_message=response_codes.MESSAGE_SUCCESS,
            response_data=[
                obj.display() for obj in cls.db_read_records(read_filter=data, deleted_records=False).limit(1)
            ])

    @classmethod
    def read_last(cls, data):
        # obj =  cls.db_read_single_record(read_filter=data)
        obj =  cls.db_read_single_record(read_filter=data)
        return response_utils.get_response_object(
            response_code=response_codes.CODE_SUCCESS,
            response_message=response_codes.MESSAGE_SUCCESS,
            response_data=obj.display_min()   
            )

    @classmethod
    def trigger_controller(cls, data):
            filter = {}
            if data.get(constants.ID):
                filter = {constants.ID:data[constants.ID]}
            if data.get(constants.IO_DATA__ID):
                data[constants.IO_DATA__ID] = data[constants.IO_DATA__ID][3:]
                filter = {constants.IO_DATA__ID:data[constants.IO_DATA__ID]}
            io = IoController.db_read_single_record(read_filter=filter)
            data[constants.IO_DATA__ID] = str(io[constants.ID])
            io_data = cls.db_read_single_record(read_filter={constants.IO_DATA__ID:data[constants.IO_DATA__ID]})
            io_data[constants.IO_DATA__TRIGGER] = data['data']
            obj = io_data.save()
            print(obj)
            return response_utils.get_response_object(
                response_code=response_codes.CODE_SUCCESS,
                response_message=response_codes.MESSAGE_SUCCESS,
                response_data=obj.display()
            )