# Python imports
import datetime
import time
import re
import json
import uuid
import hashlib
# import pytz
# Local imports
from esp32OTA.generic.services.utils import constants, __global__
from esp32OTA.config import config

# Framework imports
from flask import request, abort


def posted():
    """
    Get Data
    :return:
    """
    if request.method == "GET":
        return request.args or {}
    return request.get_json(silent=True) or {}


def posted_form_data():
    """
    Get Data
    :return:
    """
    return request.form or {}

def posted_files():
    """
    Get Data
    :return:
    """
    data = dict(request.form)  # form fields
    files = {key: request.files[key] for key in request.files}  # files
    data.update(files)
    return data




def raise_response_code(code):
    abort(code)


def get_time(offset=0, days=0):
    """ return serialized datetime current + offset in hours """
    # timezone = pytz.timezone(config.TIME_ZONE)
    hours = offset
    return int(time.mktime(
        (datetime.datetime.now() +
         datetime.timedelta(hours=hours, days=days)).timetuple()))*1000

def get_time_iso():
    return int(datetime.datetime.now().strftime("%H%M"))

def get_day():
    return datetime.datetime.now().isoweekday()

def format_time(seconds, format=config.DISPLAY_TIME_FORMAT):
    try:
        return "{}".format(str(datetime.timedelta(seconds=seconds)))
    except ValueError:
        return None


def format_datetime(str_datetime, format=config.DATETIME_FORMAT):
    try:
        return datetime.datetime.strptime(str(str_datetime), format)
    except ValueError:
        return None


def format_date(str_date, format=config.DATE_FORMAT):
    try:
        return datetime.datetime.strptime(str(str_date), format)
    except ValueError:
        return None


def epoch_to_datetime(epoch_time):
    try:
        date = datetime.datetime.fromtimestamp(epoch_time/1000)
        return date.strftime(config.DISPLAY_DATETIME_FORMAT)
    except ValueError:
        return None


def convert_to_epoch(str_time, format=config.DATETIME_FORMAT):
    return int(time.mktime(time.strptime(str_time, format)))

def convert_to_epoch1000(str_time, format=config.DATETIME_FORMAT):
    return int(time.mktime(time.strptime(str_time, format)))*1000

def json_to_dict(json_data):
    return json.loads(json_data)


def generate_uuid4():
    return str(uuid.uuid4())


def validate_password(password):
    if len(password) < 8:
        return [
            False,
            constants.VALIDATION_MESSAGES["PASSWORD"]["MINIMUM_LENGTH_ERROR"]]
    if not re.match('.*[a-z].*', password):
        return [False,
                constants.VALIDATION_MESSAGES["PASSWORD"]["MISSING_LOWERCASE"]]

    if not re.match('.*[A-Z].*', password):
        return [False,
                constants.VALIDATION_MESSAGES["PASSWORD"]["MISSING_UPPERCASE"]]

    if not re.match('.*[0-9].*', password):
        return [False,
                constants.VALIDATION_MESSAGES["PASSWORD"]["MISSING_NUMBER"]]

    if not re.match('.*[.~`!@#$%^&*(){};:/?<>,|*-+].*', password):
        return [False,
                constants.VALIDATION_MESSAGES["PASSWORD"]["MISSING_SPECIAL"]]

    return True, ""


def encrypt_password(password):
    """ return Encrypted Password  """
    from esp32OTA import bcrypt
    return bcrypt.generate_password_hash(password).decode('utf-8')


def verify_password(password_hash, password):
    """ return if the password_hash matches the hash or :param: password """
    from esp32OTA import bcrypt
    return bcrypt.check_password_hash(password_hash, password)


def get_access_token():
    """ Gets user token from header. """
    access_token =  request.cookies.get('access_token', None)
    session_type =  request.cookies.get('session_type', None)
    if not access_token:
        return [request.headers.get('x-session-key', None),
                request.headers.get('x-session-type', None)]
    else:
        return [access_token, session_type]

def get_token():
    access_token, token_type = get_access_token()
    if not access_token:
        return None
    from esp32OTA.UserManagement.controllers.TokenController import TokenController
    token_obj = TokenController.authenticate_token(access_token, purpose=constants.PURPOSE_LOGIN)
    if not token_obj:
        return None
    user = token_obj[constants.USER].fetch()
    __global__.set_current_user(user)
    return token_obj

def get_last_update(token):
    from esp32OTA.UserManagement.controllers.TokenController import TokenController
    token_obj = TokenController.get_token(token)
    current_time = get_time()
    if current_time - token_obj[constants.UPDATED_ON] > (config.DEVICE_OFFLINE_TIME * 60 * 1000):
        status = "offline"
    else:
        status = "online"
    last_update = epoch_to_datetime(token_obj[constants.UPDATED_ON])
    return {'last_update': last_update,
            'status': status
    }

def current_user():
    user = __global__.get_current_user()
    if user:
        return user
    token_obj = get_token()
    if token_obj:
        return token_obj[constants.TOKEN__USER].fetch()
    print('User not found')
    return None

def get_file_checksum(file, algorithm=config.CHECKSUM_ALGORITHM):
    hash_func = None
    if algorithm == "md5":
        hash_func = hashlib.md5()
    elif algorithm == "sha1":
        hash_func = hashlib.sha1()
    elif algorithm == "sha256":
        hash_func = hashlib.sha256()
    elif algorithm == "sha512":
        hash_func = hashlib.sha512()
    else:
        return None
    # Read and update hash string value in blocks of 4K
    for byte_block in iter(lambda: file.read(4096), b""):
        hash_func.update(byte_block)
    file.seek(0)
    return hash_func.hexdigest()