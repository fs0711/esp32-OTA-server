from datetime import datetime
from esp32OTA.DeviceManagement.controllers.DeviceController import DeviceController
from esp32OTA.NotificationManagement.controller.NotificationsController import NotificationController


# Define task functions at module level so they can be serialized for Redis
def update_offline_devices():
    """Update offline device status - runs every minute."""
    print(f"[{datetime.now()}] Updating offline devices...")
    DeviceController.get_last_online()


def send_notifications():
    """Send email notifications - runs every minute."""
    print(f"[{datetime.now()}] Sending notification emails...")
    NotificationController.send_notifications()


def register_scheduled_tasks(scheduler):
    """
    Register all scheduled tasks with the scheduler.
    Tasks are defined at module level to support Redis serialization.
    
    Args:
        scheduler: APScheduler instance
    """
    
    # Add tasks programmatically with textual references
    scheduler.add_job(
        id='update_offline_devices',
        func='esp32OTA.scheduled_tasks:update_offline_devices',
        trigger='interval',
        minutes=1,
        misfire_grace_time=60,
        replace_existing=True
    )
    
    scheduler.add_job(
        id='send_email_notifications',
        func='esp32OTA.scheduled_tasks:send_notifications',
        trigger='interval',
        minutes=1,
        misfire_grace_time=60,
        replace_existing=True
    )
    
    print("All scheduled tasks registered successfully!")


# Example: Additional task that runs at a specific time every day
# def generate_daily_report():
#     """Generate daily report at midnight."""
#     print(f"[{datetime.now()}] Daily report task executed!")
#     # Add your reporting logic here
#
# To register:
# scheduler.add_job(
#     id='daily_report',
#     func='esp32OTA.scheduled_tasks:generate_daily_report',
#     trigger='cron',
#     hour=0,
#     minute=0,
#     misfire_grace_time=900,
#     replace_existing=True
# )
