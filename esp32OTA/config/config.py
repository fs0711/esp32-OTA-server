# Python imports
import os
# Local imports


# ENVIRONMENT = "LOCAL"
ENVIRONMENT = os.environ.get("APP_ENVIRONMENT", "LOCAL")

FUNCTION_LOGGING = False

current_dir_path = os.path.dirname(os.path.abspath(__file__))
static_data_path = os.path.join(current_dir_path, "static//static_data.json")
upload_files_path = os.path.join(os.getcwd(), "//uploads")

log_directory_path = "/var/log/esp32ota"

#  EXPIRY TIME IN HOURS
TOKEN_EXPIRY_TIME_WEB = 6
TOKEN_EXPIRY_TIME_MOBILE = 30 #days
TOKEN_EXPIRY_TIME_DEVICE = 365 #days
# TOKEN_EXPIRY_TIME_EMAIL = 0.5
DEVICE_OFFLINE_TIME = 10 #minutes


CHECKSUM_ALGORITHM = "sha256"

FIREBASE_CONFIG = {}

FCM_API_KEY = ""

DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
FULL_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S.%f%z"
DISPLAY_DATETIME_FORMAT = "%d-%m-%Y %H:%M:%S"
DISPLAY_DATE_FORMAT = "%d-%m-%Y"
DISPLAY_TIME_FORMAT = "%H:%M:%S"
FILTER_DATE_FORMAT = "%d %m %Y"
FILTER_DATETIME_FORMAT = "%d %m %Y %H:%M:%S"
TIME_ZONE = "Asia/Karachi"

FRONTEND_URL = "https://iot.digtrosoft.com"
MONGO_DB_USER = "zvolta_admin"
MONGO_DB_PASSWORD = "Frig3ahpHed9kUMJ"
DATABASE_NAME = "ESP32OTA"

MONGO_DB_URI = ""
if ENVIRONMENT == "LOCAL":
    MONGO_DB_URI = f"mongodb://localhost:27017/{DATABASE_NAME}"
if ENVIRONMENT == "STAGING":
    FUNCTION_LOGGING = True
    static_data_path = os.path.join(
        current_dir_path, "static/static_data.json")
    upload_files_path = os.path.join(current_dir_path, "static/uploads")
    # MONGO_DB_URI = f"mongodb://192.168.100.8:27017/ppbackend"
    MONGO_DB_URI = f"mongodb+srv://{MONGO_DB_USER}:{MONGO_DB_PASSWORD}@zvolta-free.pp59hoj.mongodb.net/{DATABASE_NAME}"
    #     "retryWrites=true&w=majority"

DEFAULT_ADMIN_NAME = "Admin"
DEFAULT_ADMIN_EMAIL = "admin@mail.com"
DEFAULT_ADMIN_PASSWORD = "Alchohol@123"
DEFAULT_ADMIN_PHONE = "+923568596321"
DEFAULT_ADMIN_ORGANIZATION = "MUNAS"
DEFAULT_ADMIN_ADDRESS = "HQ"
DEFAULT_ADMIN_CITY = "Karachi"
DEFAULT_ADMIN_COUNTRY = "Pakistan"

# EMAIL_USER = "ppBackend316@gmail.com"
# EMAIL_PASSWORD = "ppbackend123"

MAIL_SETTINGS = {
    "MAIL_SERVER": 'smtp.gmail.com',
    "MAIL_PORT": 465,
    "MAIL_USE_TLS": False,
    "MAIL_USE_SSL": True,
    "MAIL_USERNAME": "support@zvolta.com",
    "MAIL_PASSWORD": "Okayker$123"
}

NOTIFICATION_MAIL_LIST = [
    "iot@zvolta.com"
]