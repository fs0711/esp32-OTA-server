# Python imports

# Framework imports
from flask import Blueprint, render_template, request, redirect

# Local imports
from esp32OTA.UserManagement.controllers.UserController import UserController
from esp32OTA.generic.services.utils import constants, decorators, response_codes, response_utils, common_utils
from esp32OTA import app
from esp32OTA.config import config


users_bp = Blueprint("users_bp", __name__)

@app.after_request
def refresh_expiring_tokens(response):
    try:
        token_obj = common_utils.get_token()
        if not token_obj:
            return response
        if token_obj.platform == constants.PLATFORM_WEB:
            current_timestamp = common_utils.get_time()
            if not(current_timestamp > token_obj.expiry_time):
                token_obj.expiry_time = common_utils.get_time(
                    offset=config.TOKEN_EXPIRY_TIME_WEB)
                token_obj.save()
            else:
                token_obj.is_expired = True
                token_obj.save()
                return response_utils.get_response_object(
                    response_code=response_codes.CODE_HTTP_401,
                    response_message=response_codes
                    .MESSAGE_AUTHENTICATION_FAILED)
        if token_obj.platform == constants.PLATFORM_MOBILE:
            current_timestamp = common_utils.get_time()
            if not(current_timestamp > token_obj.expiry_time):
                token_obj.expiry_time = common_utils.get_time(
                    days=config.TOKEN_EXPIRY_TIME_MOBILE)
                token_obj.save()
            else:
                token_obj.is_expired = True
                token_obj.save()
                return response_utils.get_response_object(
                    response_code=response_codes.CODE_HTTP_401,
                    response_message=response_codes
                    .MESSAGE_AUTHENTICATION_FAILED)
        return response
    except (RuntimeError, KeyError):
        return response

@users_bp.route("/login/<platform>", methods=["POST"])
@decorators.logging
@decorators.keys_validator(constants.LOGIN_REQUIRED_FIELDS_LIST, [],
                           request_form_data=False)
def loginmobile_user_view(data, platform):
    data = common_utils.posted()
    return UserController.login_controller(data=data, platform=platform)


@users_bp.route("/create", methods=["POST"])
@decorators.logging
@decorators.is_authenticated
@decorators.roles_allowed([constants.ROLE_ID_ADMIN])
@decorators.keys_validator(
    constants.REQUIRED_FIELDS_LIST__USER,
    constants.OPTIONAL_FIELDS_LIST__USER,
)
def create_view(data):
    return UserController.create_controller(data=data)


@users_bp.route("/read", methods=["GET"])
@decorators.is_authenticated
@decorators.roles_allowed([constants.ROLE_ID_ADMIN])
@decorators.keys_validator(
    [],
    constants.ALL_FIELDS_LIST__USER,
)
def read_view(data):
    res = UserController.read_controller(data=data)
    return res


@users_bp.route("/update", methods=["GET","POST"])
@decorators.is_authenticated
@decorators.roles_allowed([constants.ROLE_ID_ADMIN])
@decorators.keys_validator(
    [],
    constants.ALL_FIELDS_LIST__USER,
)
def update_view(data):
    if request.method == "POST":
        res = UserController.update_controller(data)
        return redirect("/read")
    data = request.args
    users = UserController.get_user_childs(
        common_utils.current_user())
    roles = constants.DEFAULT_ROLE_OBJECTS
    data = UserController.read_controller(data={constants.ID:data[constants.ID]})
    res = {}
    res["user"] = data["response_data"][0]
    res["all-users"] = [{"id":str(user[constants.ID]), "name":user[constants.USER__NAME]} for user in users]
    res["roles"] = [{"id":role["user_role_id"], "title": role["title"]} for role in roles]
    data["response_data"] = res
    return render_template("edituser.html", **data)


@users_bp.route("/suspend", methods=["GET"])
@decorators.is_authenticated
@decorators.roles_allowed([constants.ROLE_ID_ADMIN])
@decorators.keys_validator(
    [constants.ID],
    request_form_data=False
)
def suspend_view(data):
    res = UserController.suspend_controller(data=data)
    return redirect("/read")


@users_bp.route("/restore", methods=["GET"])
@decorators.is_authenticated
@decorators.roles_allowed([constants.ROLE_ID_ADMIN])
@decorators.keys_validator(
    [constants.ID],
    request_form_data=False
)
def restore_view(data):
    res = UserController.restore_controller(data=data)
    return redirect("/read")


# @users_bp.route("/", methods=["GET"])
# @decorators.logging
# @decorators.keys_validator()
# def logined_user_view(data):
#     return render_template("login.html", Response=response_utils.get_response_object())


# @users_bp.route("/", methods=["POST"])
# @decorators.logging
# @decorators.keys_validator(constants.LOGIN_REQUIRED_FIELDS_LIST, [])
# def login_user_view(data):
#     res = UserController.login_controller(data=data)
#     return render_template("login.html", **res)



@users_bp.route("/logout", methods=["GET"])
@decorators.logging
@decorators.is_authenticated
@decorators.keys_validator()
def logout_user_view(_):
    res = UserController.logout_controller()
    return render_template("logout.html", **res)


@users_bp.route("/getuserchilds", methods=["GET"])
@decorators.logging
@decorators.is_authenticated
@decorators.keys_validator()
def get_user_childs_view(_):
    return UserController.get_users_childs_list()


@users_bp.route("/change_password", methods=["POST"])
@decorators.logging
@decorators.is_authenticated
@decorators.keys_validator(
    [constants.USER__OLD_PASSWORD,
     constants.USER__PASSWORD]
)
def change_password(data):
    # data = request.form
    res = UserController.update_controller(data=data)
    return render_template("changepassword.html", **res)