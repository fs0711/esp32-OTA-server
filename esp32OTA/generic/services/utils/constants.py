# Python imports
import json

# Local imports
from esp32OTA import config


# Reading Static Data
static_data = {}
with open(config.static_data_path, "r") as static_data_file:
    static_data = json.load(static_data_file)

# Validation Response Messages
VALIDATION_MESSAGES = {
    "REQUIRED": "{} is required",
    "NONEXISTENT": "{} should not be provided",
    "UNIQUE": "{} has to be unique",
    "EXISTS": "{} with this {} does not exist",
    "PASSWORD": {
        "MINIMUM_LENGTH_ERROR": "{} must contain minimum 8 characters",
        "MISSING_LOWERCASE": "{} must contain a single LowerCase character",
        "MISSING_UPPERCASE": "{} must contain a single UpperCase character",
        "MISSING_NUMBER": "{} must contain a single Number",
        "MISSING_SPECIAL": "{} must contain a single Special character",
    },
    "UID": "Please Enter a Valid {}",
    "EMAIL": "Please Enter a Valid {}",
    "PHONE_NUMBER": "Please Enter a Valid {}",
    "DATATYPE": "The Field {} has to be a type of {}",
    "DATETIME_FORMAT": "The Field {} should be in valid Date Time Format i.e "
    + config.DATETIME_FORMAT,
    "DATE_FORMAT": "The Field {} has to contain a valid Date Format i.e "
    + config.DATE_FORMAT,
    "CHOICES": "The Field {} has to be a value in {}",
    "LENGTH": "The Field {} has to be of length {}",
    "MAX_LENGTH": "The Length of Field {} has to be less than {}",
    "MIN_LENGTH": "The Length of Field {} has to be greater than {}",
    "FORMAT": "The Format of Field {} is incorrect Errors : {}",
}

# Validation constants
GENDER_LIST = static_data["gender"]
# Default Validation of Data before it is inserted into the database
DEFAULT_VALIDATION = True
# Default if to read is_deleted = True records from database
DEFAULT_READ_DELETED_RECORDS = False
# Update modes Database Layer
UPDATE_MODE__FULL = "full"
UPDATE_MODE__PARTIAL = "partial"

# DEFAULT OBJECTS
OBJECT_STATUS_ACTIVE = static_data["statuses"][0]
OBJECT_STATUS_INACTIVE = static_data["statuses"][1]
OBJECT_STATUS_SUSPENDED = static_data["statuses"][2]
# DEFAULT ROLES
DEFAULT_ADMIN_ROLE_OBJECT = static_data["user_roles_and_rights"][0]
DEFAULT_OWNER_ROLE_OBJECT = static_data["user_roles_and_rights"][1]
DEFAULT_MANAGER_ROLE_OBJECT = static_data["user_roles_and_rights"][2]
DEFAULT_AM_ROLE_OBJECT = static_data["user_roles_and_rights"][3]
DEFAULT_USER_ROLE_OBJECT = static_data["user_roles_and_rights"][4]
DEFAULT_ROLE_OBJECTS = [
    DEFAULT_ADMIN_ROLE_OBJECT,
    DEFAULT_OWNER_ROLE_OBJECT,
    DEFAULT_MANAGER_ROLE_OBJECT,
    DEFAULT_AM_ROLE_OBJECT,
    DEFAULT_USER_ROLE_OBJECT
]

OBJECT_STATUS_ACTIVE_ID = 1
OBJECT_STATUS_INACTIVE_ID = 2
OBJECT_STATUS_SUSPENDED_ID = 3


# STARTING
STATIC_DATA = static_data

SEARCH_DEPTH_MAX = 4

# USER TYPES
ADMIN = "admin"
OWNER = "owner"
MANAGER = "manager"
AM = "am"
USER = "user"

# USER ROLE IDS
ROLE_ID_ADMIN = 1
ROLE_ID_OWNER = 2
ROLE_ID_MANAGER = 3
ROLE_ID_AM = 4
ROLE_ID_USER = 5

# ENDING


ID = "id"
STATUS = "status"
STATUS__ID = "id"
STATUS__NAME = "name"
CREATED_ON = "created_on"
UPDATED_ON = "updated_on"
CREATED_BY = "created_by"
UPDATED_BY = "updated_by"
ASSIGNED_TO = "assigned_to"
ASSIGNED_BY = "assigned_by"


CURRENT_TIME = "current_time"

ADDRESS__COUNTRY = "country"
ADDRESS__PROVINCE = "province"
ADDRESS__CITY = "city"
ADDRESS__AREA = "area"
ADDRESS__STREET_ADDRESS = "street_address"
ADDRESS__ZIP_CODE = "zip_code"

ADDRESS_VALIDATION_FORMAT = {
    "key": [
        {
            "rule": "choices",
            "options": [
                ADDRESS__COUNTRY,
                ADDRESS__CITY,
                ADDRESS__ZIP_CODE,
                ADDRESS__STREET_ADDRESS,
            ],
        }
    ],
    "value": [{"rule": "required"}, {"rule": "datatype", "datatype": str}],
}

FILTER__NEW = "new"
FILTER__OLD = "old"
FILTER_LIST = [FILTER__NEW, FILTER__OLD]

# USER LOGIN CHANNELS
EMAIL = "email"
PHONE = "phone"
LOGGED_IN_USER = "logged_in_user"
PLATFORM_WEB = 'web'
PLATFORM_MOBILE = 'mobile'
PLATFORM_DEVICE = 'iot'
PURPOSE_LOGIN = "login-user"
PURPOSE_RESET_PASSWORD = "reset-password"
PURPOSE_IOT = "iot"

# Change Password Email
PLATFORM_EMAIL = 'email'


# USER CONSTANTS
USER = "user"
USER__NAME = "name"
USER__EMAIL_ADDRESS = "email_address"
USER__PHONE_NUMBER = "phone_number"
USER__PASSWORD = "password"
USER__OLD_PASSWORD = "old_password"
USER__GENDER = "gender"
USER__NIC = "nic"
USER__ROLE = "role"
USER__MANAGER = "manager"
USER__ROLE__ROLE_ID = "user_role_id"
USER__ROLE__NAME = "name"
USER__ROLE__TITLE = "title"
USER__ROLE__RIGHTS = "rights"
USER__ROLE__MANAGER = "manager"
USER__ROLE__MANAGER_ID = "manager_id"
USER__ROLE__MANAGER_NAME = "manager_name"

USER__NEW_PASSWORD = "new_password"
USER__OLD_PASSWORD = "old_password"


# TOKEN Constants
TOKEN = "token"
TOKEN__ACCESS_TOKEN = "access_token"
TOKEN__USER = "user"
TOKEN__PURPOSE = "purpose"
TOKEN__EXPIRY_TIME = "expiry_time"
TOKEN__IS_EXPIRED = "is_expired"
TOKEN__IS_REVOKED = "is_revoked"
TOKEN__PLATFORM = "platform"

# Required, Optional Fields Lists
# User
LOGIN_REQUIRED_FIELDS_LIST = [USER__EMAIL_ADDRESS, USER__PASSWORD]
REQUIRED_FIELDS_LIST__USER = [
    USER__NAME,
    USER__EMAIL_ADDRESS,
    USER__PASSWORD,
    USER__GENDER,
    USER__ROLE,
]

OPTIONAL_FIELDS_LIST__USER = [
    USER__EMAIL_ADDRESS,
    USER__PHONE_NUMBER,
    USER__MANAGER]

REQUIRED_UPDATE_FIELDS_LIST__USER = list(
    set(REQUIRED_FIELDS_LIST__USER + [ID])
    - set([USER__PASSWORD, USER__EMAIL_ADDRESS, USER__PHONE_NUMBER])
)
ALL_FIELDS_LIST__USER = OPTIONAL_FIELDS_LIST__USER + \
    REQUIRED_FIELDS_LIST__USER + [ID]
UPDATE_FIELDS_LIST__USER = list(
    set(REQUIRED_FIELDS_LIST__USER + [ID]))



#Device Constants
DEVICE = "device"
DEVICE__NAME = "name"
DEVICE__ID = "device_id"
DEVICE__TYPE = "device_type"
DEVICE__VARIABLES = "variables"
DEVICE__LAST_UPDATED = "last_updated"
DEVICE__ACCESS_TOKEN = "access_token"
DEVICE__HARDWARE_VERSION = "hw_version"
DEVICE__FIRMWARE_VERSION = "fw_version"
DEVICE__NEW_FIRMWARE_VERSION = "new_fw_version"
DEVICE__ROLLBACK = "rollback"
DEVICE__UPDATE_CONFIG = "update_config"
DEVICE__FIRMWARE_FILE = "fw_file"
DEVICE__UPDATE_PATH = "update_path"
DEVICE__SERIAL_NUMBER = "serial_number"
DEVICE__WIFI_MAC = "wifi_mac"
DEVICE__BT_MAC = "bt_mac"
DEVICE__IMEI = "imei"
DEVICE__QR_CODE = "qr_code"
DEVICE__CONNECTION = "connection"


REQUIRED_FIELDS_LIST__DEVICE = [
    DEVICE__TYPE
]

OPTIONAL_FIELDS_LIST__DEVICE = [
    DEVICE__VARIABLES,
    DEVICE__LAST_UPDATED,
    DEVICE__HARDWARE_VERSION,
    DEVICE__FIRMWARE_VERSION,
    DEVICE__NEW_FIRMWARE_VERSION,
    DEVICE__ROLLBACK,
    DEVICE__UPDATE_CONFIG,
    DEVICE__FIRMWARE_FILE,
    DEVICE__UPDATE_PATH,
    DEVICE__WIFI_MAC,
    DEVICE__BT_MAC,
    DEVICE__IMEI,
    DEVICE__QR_CODE,
    DEVICE__NAME
]

UPDATE_FIELDS_LIST__DEVICE = list(
    set(REQUIRED_FIELDS_LIST__DEVICE + OPTIONAL_FIELDS_LIST__DEVICE + [ID]))

ALL_FIELDS_LIST__DEVICE = list(
    set(REQUIRED_FIELDS_LIST__DEVICE + OPTIONAL_FIELDS_LIST__DEVICE + [ID]))


# Device Type Constants
DEVICE_TYPE = "device_type"
DEVICE_TYPE__ID = "device_type_id"
DEVICE_TYPE__DEVICE_TYPE = "device_type"
DEVICE_TYPE__TYPE_CODE = "type_code"
DEVICE_TYPE__DESCRIPTION = "description"
DEVICE_TYPE__BILL_OF_MATERIAL = "bom"

REQUIRED_FIELDS_LIST__DEVICE_TYPE = [
    DEVICE_TYPE__DEVICE_TYPE,
    DEVICE_TYPE__TYPE_CODE
]

OPTIONAL_FIELDS_LIST__DEVICE_TYPE = [
    DEVICE_TYPE__DESCRIPTION,
    DEVICE_TYPE__BILL_OF_MATERIAL
]

UPDATE_FIELDS_LIST__DEVICE_TYPE = list(
    set(REQUIRED_FIELDS_LIST__DEVICE_TYPE + [ID]))


#firmware constants
FIRMWARE = "firmware"
FIRMWARE__VERSION = "version"
FIRMWARE__FILE = "file"
FIRMWARE__FILE_NAME = "file_name"
FIRMWARE__DESCRIPTION = "description"
FIRMWARE__DEVICE_TYPE = "device_type"
FIRMWARE__RELEASED_ON = "released_on"
FIRMWARE__HARDWARE_VERSION = "hw_version"
FIRMWARE__UPDATE_PATH = "update_path"
FIRMWARE__CHECKSUM = "checksum"
FIRMWARE__UPDATE_PATH_LIST = static_data["update_path"]

REQUIRED_FIELDS_LIST__FIRMWARE = [
    FIRMWARE__VERSION,
    FIRMWARE__FILE,
    FIRMWARE__CHECKSUM,
    FIRMWARE__HARDWARE_VERSION

]

OPTIONAL_FIELDS_LIST__FIRMWARE = [
    FIRMWARE__DESCRIPTION,
    FIRMWARE__UPDATE_PATH,
    FIRMWARE__DEVICE_TYPE,
    FIRMWARE__RELEASED_ON
]

UPDATE_FIELDS_LIST__FIRMWARE = list(
    set(REQUIRED_FIELDS_LIST__FIRMWARE + OPTIONAL_FIELDS_LIST__FIRMWARE) - set([FIRMWARE__FILE, FIRMWARE__CHECKSUM]))


#Notifications
NOTIFICATION = "notification"
NOTIFICATION__READ = "read"
NOTIFICATION__SEND = "send"
NOTIFICATION__TITLE = "title"
NOTIFICATION__MESSAGE = "message"
NOTIFICATION__TYPE = "type"
NOTIFICATION__RELATED_DEVICE = "related_device"
