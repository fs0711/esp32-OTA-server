# Python imports
import re
from math import nan, isnan
# Framework imports
from flask_mail import Message

# Local imports
from ast import Constant
from esp32OTA.generic.controllers import Controller
from esp32OTA.NotificationManagement.model.Notifications import Notification
from esp32OTA.generic.services.utils import constants, response_codes, response_utils, common_utils, __global__
from esp32OTA import config
from esp32OTA import mail
from datetime import datetime


class NotificationController(Controller):
    Model = Notification

    @classmethod
    def create_controller(cls, data):
        _, _, obj = cls.db_insert_record(
                data=data, default_validation=False, user=False)
        obj.save()
        return response_utils.get_response_object(
            response_message=response_codes.MESSAGE_SUCCESS,
            response_data=obj.display(),
            response_code=response_codes.CODE_SUCCESS
        )
    
    @classmethod
    def send_notifications(cls):
        notifications = cls.db_read_records(
            read_filter={constants.NOTIFICATION__SEND: False})
        for notification in notifications:
            # Send email notification
            try:
                msg = Message(
                    subject=notification[constants.NOTIFICATION__TITLE],
                    sender=config.MAIL_SETTINGS['MAIL_USERNAME'],
                    recipients=config.NOTIFICATION_MAIL_LIST
                )
                
                # Create email body
                msg.body = f"""
                    Notification Type: {notification[constants.NOTIFICATION__TYPE]}
                    Title: {notification[constants.NOTIFICATION__TITLE]}
                    Message: {notification[constants.NOTIFICATION__MESSAGE]}
                    Time: {datetime.now().strftime(config.DISPLAY_DATETIME_FORMAT)}
                    """
                
                if notification[constants.NOTIFICATION__RELATED_DEVICE]:
                    msg.body += f"\nRelated Device: {notification[constants.NOTIFICATION__RELATED_DEVICE]}"
                
                mail.send(msg)
                print(f"Email sent successfully for notification: {notification[constants.ID]}")
            except Exception as e:
                print(f"Failed to send email for notification {notification[constants.ID]}: {str(e)}")
            
            # Mark notification as sent
            notification[constants.NOTIFICATION__SEND] = True
            notification.save()
        
        return True