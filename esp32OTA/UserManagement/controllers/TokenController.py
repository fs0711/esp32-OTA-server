# Python imports
from threading import Thread
# Framework Imports
# from flask_mail import Message
# Local imports
# from ppBackend import app
from esp32OTA.generic.controllers import Controller
from esp32OTA.UserManagement.models.Token import Token
from esp32OTA.generic.services.utils import common_utils, constants
# from ppBackend.generic.services.messages import message
# from ppBackend import config


class TokenController(Controller):
    Model = Token

    @classmethod
    def generate_access_token(cls, purpose, expiry_time, platform, user):
        access_token = common_utils.generate_uuid4()
        if platform == constants.PLATFORM_WEB:
            expiry_timestamp = common_utils.get_time(offset=expiry_time)
        if platform == constants.PLATFORM_MOBILE:
            expiry_timestamp = common_utils.get_time(days=expiry_time)
        if platform == constants.PLATFORM_DEVICE:
            expiry_timestamp = common_utils.get_time(days=expiry_time)
        return cls.db_insert_record(
            {
                constants.TOKEN__ACCESS_TOKEN: access_token,
                constants.TOKEN__USER: user,
                constants.TOKEN__PURPOSE: purpose,
                constants.TOKEN__EXPIRY_TIME: expiry_timestamp,
                constants.TOKEN__IS_EXPIRED: False,
                constants.TOKEN__IS_REVOKED: False,
                constants.TOKEN__PLATFORM: platform
            }
        )
        
    @classmethod
    def authenticate_token(cls, access_token, purpose=None):
        data = {constants.TOKEN__ACCESS_TOKEN: access_token,
                constants.TOKEN__IS_EXPIRED: False,
                constants.TOKEN__IS_REVOKED: False}
        if purpose:
            data.update({constants.TOKEN__PURPOSE: purpose})
        return cls.db_read_single_record(data)

    @classmethod
    def get_token(cls, access_token):
        data = {constants.TOKEN__ACCESS_TOKEN: access_token}
        return cls.db_read_single_record(data)

    @classmethod
    def get_active_session_token(cls, user):
        data = {
            constants.TOKEN__USER: user,
            constants.TOKEN__PURPOSE: constants.PURPOSE_LOGIN,
            constants.TOKEN__IS_EXPIRED: False,
            constants.TOKEN__IS_REVOKED: False
        }
        return cls.db_read_records(data)

    @classmethod
    def revoke_token(cls, access_token):
        return cls.db_update_single_record({
            constants.TOKEN__ACCESS_TOKEN: access_token},
            {constants.TOKEN__IS_REVOKED: True},
            update_mode=constants.UPDATE_MODE__PARTIAL)

    @classmethod
    def suspend_user_tokens(cls, read_filter):
        return cls.db_update_records(read_filter=read_filter, update_filter={
            constants.TOKEN__IS_REVOKED: True}, default_validation=False)

    # @classmethod
    # def send_forgot_password_email(cls, user):
    #     email_token_object = cls.db_read_single_record({
    #         constants.TOKEN__USER: user,
    #         constants.TOKEN__IS_EXPIRED: False,
    #         constants.TOKEN__IS_REVOKED: False,
    #         "expiry_time__gt": common_utils.get_time(),
    #         constants.TOKEN__PURPOSE:constants.PURPOSE_RESET_PASSWORD
    #     })
    #     # If the link exist expire it.
    #     if email_token_object:
    #         email_token_object[constants.TOKEN__IS_REVOKED] = True
    #         email_token_object.save()

    #     _, _, token_obj = cls.db_insert_record(data={
    #         constants.TOKEN__ACCESS_TOKEN: common_utils.generate_uuid4(),
    #         constants.TOKEN__USER: user,
    #         constants.TOKEN__PURPOSE: constants.PURPOSE_RESET_PASSWORD,
    #         constants.TOKEN__EXPIRY_TIME: common_utils.get_time(
    #             offset=config.TOKEN_EXPIRY_TIME_EMAIL),
    #         constants.TOKEN__IS_EXPIRED: False,
    #         constants.TOKEN__IS_REVOKED: False
    #     })
    #     verification_link = "/reset-password?uid={}&token={}"
    #     email_verification_url = config.FRONTEND_URL + \
    #         (verification_link.format(user.uid,
    #          token_obj[constants.TOKEN__ACCESS_TOKEN]))

    #     thread = Thread(target=send_email, args=(
    #         message.EMAIL_RESET_PASSWORD_SUBJECT, user.email_address,
    #         message.EMAIL_RESET_PASSWORD_BODY.format(
    #             user.name, email_verification_url)))
    #     thread.start()


# def send_email(subject, recipients, body):
#     """
#     This function will send out an email
#     :param subject:
#     :param recipients:
#     :param body:
#     :return:
#     """
#     with app.app_context():
#         msg = Message(subject=subject,
#                       sender=config.EMAIL_USER,
#                       recipients=[recipients],
#                       body=body)
#         mail.send(msg)
