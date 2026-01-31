# Framework imports
from flask import Flask
from flask_moment import Moment
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from flask_mail import Mail
# Local imports
from esp32OTA.generic.database import initialize_db
from esp32OTA.config import config


def register_scripts():
    from esp32OTA.scripts import run_scripts
    run_scripts(execute_create_admin_user_if_not_exists=True)
    # Routing
    import esp32OTA.urls


# application objects
app = Flask(__name__)
CORS(app)
app.config["MONGODB_HOST"] = config.MONGO_DB_URI
app.config["UPLOAD_FOLDER"] = config.upload_files_path
initialize_db(app)
moment = Moment(app)
bcrypt = Bcrypt(app)
app.config.update(config.MAIL_SETTINGS)
mail = Mail(app)
register_scripts()

# Initialize scheduler for background tasks
from esp32OTA.scheduler import init_scheduler
init_scheduler(app)