import os

# Set environment variable for the application
os.environ["APP_ENVIRONMENT"] = "STAGING"

bind = "unix:esp32ota.sock"
workers = 5
accesslog = "/var/log/esp32ota/access.log"
errorlog = "/var/log/esp32ota/error.log"
umask = 7