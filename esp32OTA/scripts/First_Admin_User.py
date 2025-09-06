# Date Created 14/09/2021 17:05:00


# Local imports
from esp32OTA import app
from esp32OTA.config import config
from esp32OTA.generic.services.utils import common_utils, constants
from esp32OTA.UserManagement.controllers.UserController import UserController

# from ppBackend.UserManagement.controllers.RoleController\
#     import RoleController


def create_admin_user_if_not_exists(run=False):
    if not run:
        return
    with app.test_request_context():
        if not bool(UserController.db_read_records({}).count()):
            print("No Users")
            # if not bool(RoleController.db_read_records({
            #         "category": constants.DEFAULT_ADMIN_ROLE_OBJECT}).count()):
            #     _, _, role = RoleController.db_insert_record({
            #         "name": "Admin",
            #         "category": constants.DEFAULT_ADMIN_ROLE_OBJECT})
            # else:
            #     role = RoleController.db_read_single_record(
            #         {"category": constants.DEFAULT_ADMIN_ROLE_OBJECT})
            is_valid, error_messages, obj = UserController.db_insert_record(
                data={
                    constants.USER__NAME: config.DEFAULT_ADMIN_NAME,
                    constants.USER__EMAIL_ADDRESS: config.DEFAULT_ADMIN_EMAIL,
                    constants.USER__PASSWORD:  common_utils.encrypt_password(password=config.DEFAULT_ADMIN_PASSWORD),
                    constants.USER__PHONE_NUMBER: config.DEFAULT_ADMIN_PHONE,
                    constants.USER__GENDER: constants.GENDER_LIST[0],
                    constants.USER__NIC: "abcNic",
                    constants.USER__ROLE: constants.DEFAULT_ADMIN_ROLE_OBJECT
                }
            )
            if not is_valid:
                print(error_messages)
            print(obj.to_json())
