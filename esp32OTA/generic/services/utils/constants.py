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
USER__ORGANIZATION = "organization"
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
    USER__ORGANIZATION
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


# Client Constants
CLIENT = "client"
CLIENT__ID = "client_id"
CLIENT__NAME = "name"
CLIENT__CONTACT_PERSON = "contact_person"
CLIENT__CP_PHONE_NUMBER = "cp_phone_number"
CLIENT__CP_EMAIL_ADDRESS = "cp_email_address"
CLIENT__CITY = "city"
CLIENT__ZIPCODE = "zipcode"
CLIENT__COUNTRY = "country"
CLIENT__ORGANIZATION = "organization"

REQUIRED_FIELDS_LIST__CLIENTS = [
    CLIENT__NAME,
    CLIENT__COUNTRY,
    CLIENT__CITY,
    CLIENT__ORGANIZATION
]

OPTIONAL_FIELDS_LIST__CLIENTS = [
    CLIENT__CONTACT_PERSON,
    CLIENT__CP_EMAIL_ADDRESS,
    CLIENT__CP_PHONE_NUMBER,
    CLIENT__ZIPCODE
]

# Sites
SITE = "site"
SITE__ID = "site_id"
SITE__NAME = "name"
SITE__ADDRESS = "address"
SITE__CITY = "city"
SITE__COUNTRY = "country"
SITE__ZIPCODE = "zipcode"
SITE__CLIENT = "client"
SITE__CONTACT_PERSON = "contact_person"
SITE__CP_EMAIL_ADDRESS = "cp_email_address"
SITE__CP_PHONE_NUMBER = "cp_phone_number"

REQUIRED_FIELDS_LIST__SITE = [
    SITE__NAME,
    SITE__ADDRESS,
    SITE__CITY,
    SITE__COUNTRY,
    SITE__ZIPCODE,
    SITE__CLIENT
]

OPTIONAL_FIELDS_LIST__SITE = [
    SITE__CONTACT_PERSON,
    SITE__CP_EMAIL_ADDRESS,
    SITE__CP_PHONE_NUMBER
]


# organization Constants
ORGANIZATION = "organization"
ORGANIZATION__NAME='name'
ORGANIZATION__ADDRESS='address'
ORGANIZATION__CITY='city'
ORGANIZATION__COUNTRY= 'country'
ORGANIZATION__CP_NAME= 'cp_name'
ORGANIZATION__CP_EMAIL= 'cp_email_address'
ORGANIZATION__CP_PHONE_NUMBER= 'cp_phone_number'
ORGANIZATION__NTN = 'ntn'
ORGANIZATION__CUSTOM_FIELDS = "custom_fields"


#Organizations Record Field

REQUIRED_FIELDS_LIST__ORGANIZATION = [
    ORGANIZATION__NAME, 
    ORGANIZATION__CP_NAME,
    ORGANIZATION__CP_EMAIL,
    ORGANIZATION__CP_PHONE_NUMBER,
    ORGANIZATION__ADDRESS,
    ORGANIZATION__CITY,
    ORGANIZATION__COUNTRY,
] 

OPTIONAL_FIELDS_LIST__ORGANIZATION =[
    ORGANIZATION__NTN,
    ORGANIZATION__CUSTOM_FIELDS
]

UPDATE_FIELDS_LIST__ORGANIZATION = list(
    set(REQUIRED_FIELDS_LIST__ORGANIZATION + [ID]))


#Device Constants
DEVICE = "device"
DEVICE__NAME = "name"
DEVICE__ID = "device_id"
DEVICE__TYPE = "type"
DEVICE__VARIABLES = "variables"
DEVICE__INPUTS = "inputs"
DEVICE__OUTPUTS = "outputs"
DEVICE__CLIENT = "client"
DEVICE__SITE = "site"
DEVICE__LAST_UPDATED = "last_updated"
DEVICE__ORGANIZATION = "organization"
DEVICE__ACCESS_TOKEN = "access_token"
DEVICE__TYPE_LIST = static_data["device_types"]

REQUIRED_FIELDS_LIST__DEVICE = [
    DEVICE__NAME,
    DEVICE__TYPE,
    DEVICE__CLIENT,
    DEVICE__SITE,
    DEVICE__ORGANIZATION
]

OPTIONAL_FIELDS_LIST__DEVICE = [
    DEVICE__VARIABLES,
    DEVICE__INPUTS,
    DEVICE__OUTPUTS
]

UPDATE_FIELDS_LIST__DEVICE = list(
    set(REQUIRED_FIELDS_LIST__DEVICE + [ID]))


#IO constants
IO = "io"
IO__NAME = "name"
IO__ID = "io_id"
IO__TYPE = "type"
IO__DEVICE = "device"
IO__DATA_TYPE = "data_type"
IO__UNIT = "unit"
IO__DISPLAY = "display_type"
IO__DISPLAY_LIST = static_data["display_types"]
IO__TYPE_LIST = static_data["IO_types"]
IO__DATA_TYPE_LIST = static_data["data_types"]

REQUIRED_FIELDS_LIST__IO = [
    IO__NAME,
    IO__TYPE,
    IO__DATA_TYPE,
    IO__DEVICE,
]

OPTIONAL_FIELDS_LIST__IO = [
    IO__UNIT,
    IO__DISPLAY
]


#IO Data constants
IO_DATA = "io_data"
IO_DATA__ID = "io_id"
IO_DATA__VAL_INT = "val_int"
IO_DATA__VAL_FLOAT = "val_float"
IO_DATA__VAL_STR = "val_str"
IO_DATA__VAL_BOOL = "val_bool"
IO_DATA__DATA = "data"
IO_DATA__TRIGGER = "trigger"
IO_DATA__SCHEDULE = "schedule"

REQUIRED_FIELDS_LIST__IO_DATA = [
    IO_DATA__DATA
]

OPTIONAL_FIELDS_LIST__IO_DATA = [
    ID,
    IO_DATA__ID,
    IO_DATA__VAL_BOOL,
    IO_DATA__VAL_FLOAT,
    IO_DATA__VAL_INT,
    IO_DATA__VAL_STR
]


#Schedule constants
SCHEDULE = "schedule"
SCHEDULE__DAY = "day"
SCHEDULE__START_TIME = "start_time"
SCHEDULE__END_TIME = "end_time"
SCHEDULE__DURATION = "duration"
SCHEDULE__IO_ID = "io_id"

REQUIRED_FIELDS_LIST__SCHEDULE = [
    SCHEDULE__START_TIME,
    SCHEDULE__IO_ID,
    SCHEDULE__DAY,
    SCHEDULE__DURATION
]

OPTIONAL_FIELDS_LIST__SCHEDULE = [
    SCHEDULE__DURATION,
    SCHEDULE__END_TIME
]