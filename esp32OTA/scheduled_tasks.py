from datetime import datetime
from esp32OTA.DeviceManagement.controllers.DeviceController import DeviceController
from esp32OTA.NotificationManagement.controller.NotificationsController import NotificationController
from esp32OTA.Services.GatewayService import GatewayService
import os

def register_scheduled_tasks(scheduler):
    """
    Register all scheduled tasks with the scheduler.
    
    Args:
        scheduler: APScheduler instance
    """

    @scheduler.task('interval', id='update_offline_devices', minutes=1, misfire_grace_time=60)
    def update_offline_devices():
        print(f"[{datetime.now()}] Updating offline devices...")
        DeviceController.get_last_online()

    @scheduler.task('interval', id='Email Notifications', minutes=1, misfire_grace_time=60)
    def Send_notifications():
        print(f"[{datetime.now()}] Sending notification emails...")
        NotificationController.send_notifications()
        
    @scheduler.task('interval', id='gateway_device_polling', seconds=60, misfire_grace_time=120, max_instances=5)
    def gateway_poll_task():
        GatewayService.poll_devices()

    # # Example 3: Task that runs at a specific time every day
    # @scheduler.task('cron', id='daily_report', hour=0, minute=0, misfire_grace_time=900)
    # def generate_daily_report():
    #     """Generate daily report at midnight."""
    #     print(f"[{datetime.now()}] Daily report task executed!")
    #     # Add your reporting logic here
    
    
    # # Example 4: Task that runs every Monday at 9 AM
    # @scheduler.task('cron', id='weekly_task', day_of_week='mon', hour=9, minute=0, misfire_grace_time=900)
    # def weekly_maintenance():
    #     """Weekly maintenance task."""
    #     print(f"[{datetime.now()}] Weekly maintenance task executed!")
    #     # Add your weekly maintenance logic here
    
    
    print("All scheduled tasks registered successfully!")


# You can also define standalone task functions and add them programmatically
# def custom_task():
#     """A custom task that can be added programmatically."""
#     print(f"[{datetime.now()}] Custom task executed!")


# To add tasks programmatically (optional):
# scheduler.add_job(
#     id='custom_task_id',
#     func=custom_task,
#     trigger='interval',
#     seconds=60,
#     replace_existing=True
# )
