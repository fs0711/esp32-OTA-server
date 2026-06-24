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

    # @scheduler.task('interval', id='update_offline_devices', minutes=1, misfire_grace_time=60)
    # def update_offline_devices():
    #     print(f"[{datetime.now()}] Updating offline devices...")
    #     DeviceController.get_last_online()

    # @scheduler.task('interval', id='Email Notifications', minutes=1, misfire_grace_time=60)
    # def Send_notifications():
    #     print(f"[{datetime.now()}] Sending notification emails...")
    #     NotificationController.send_notifications()
        

    @scheduler.task('interval', id='server_heartbeat', seconds=120, misfire_grace_time=60, max_instances=1)
    def server_heartbeat_task():
        """Send heartbeat every 120 seconds to report device status to API."""
        GatewayService.send_heartbeat()

    @scheduler.task('interval', id='check_device_status', seconds=110, misfire_grace_time=60, max_instances=1)
    def check_device_status_task():
        """Check and update device online/offline status every 110 seconds based on last_updated timestamp."""
        GatewayService.check_and_update_device_status()

    @scheduler.task('interval', id='check_stale_usage', seconds=30, misfire_grace_time=30, max_instances=1)
    def check_stale_usage_task():
        """Auto-complete usage sessions stuck at is_completed=0 for more than 3 minutes."""
        from esp32OTA.Services.mqtt_client import mqtt_service
        # mqtt_service.check_stale_usage_completions()

    print("All scheduled tasks registered successfully!")

