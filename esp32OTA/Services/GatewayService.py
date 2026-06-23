import time
import logging
import requests
import json
import os
import subprocess
from datetime import datetime, timedelta, timezone
from esp32OTA.DeviceManagement.models.Device import Device
from esp32OTA.generic.services.utils import constants
from esp32OTA.Services.mqtt_client import mqtt_service

logger = logging.getLogger(__name__)

class GatewayService:
    _last_data = {}  # Store last received data for dashboard
    _last_status = {} # Store last status for check-then-publish logic
    _max_logs = 100
    _last_heartbeat_time = 0

    
    @classmethod
    def get_broker_stats(cls):
        """Returns broker stats from the dedicated MQTT service."""
        return mqtt_service.broker_stats

    @classmethod
    def get_mqtt_status(cls):
        """Checks if the internal MQTT service is connected."""
        return mqtt_service.client.is_connected()

    @classmethod
    def get_live_logs(cls):
        """Reads the Mosquitto log file and returns last cached lines."""
        log_path = "/home/shaheer/mosquitto-auth.log"
        if not os.path.exists(log_path):
            return ["Log file not found at " + log_path]
        
        try:
            # Use powershell if on windows, tail -n if on linux
            if os.name == 'nt':
                # Simplified check for Windows environment
                return ["Log viewing is optimized for Linux/Unix systems."]
            
            result = subprocess.check_output(['tail', '-n', str(cls._max_logs), log_path], stderr=subprocess.STDOUT)
            return result.decode('utf-8').splitlines()
        except Exception as e:
            return [f"Error reading logs: {str(e)}"]

   
    @classmethod
    def check_and_update_device_status(cls):
        """
        Checks all devices' last_updated timestamps and updates their status to online/offline.
        If last_updated is within 1 minute: status = online
        If last_updated is more than 1 minute ago: status = offline
        """
        try:
            from datetime import datetime, timezone

            current_time = datetime.now()  # naive local time — matches stored last_updated format
            threshold_seconds = 60  # 1 minute

            devices = Device.objects()

            if not devices:
                return

            updates_count = 0

            for device in devices:
                try:
                    connection = getattr(device, 'connection', {})
                    if not connection:
                        continue

                    last_updated = connection.get('last_updated')
                    if not last_updated:
                        continue

                    # Stored format: DD-MM-YYYY HH:MM:SS (DISPLAY_DATETIME_FORMAT)
                    if isinstance(last_updated, str):
                        try:
                            last_updated_dt = datetime.strptime(last_updated, "%d-%m-%Y %H:%M:%S")
                        except ValueError:
                            last_updated_dt = datetime.fromisoformat(last_updated.replace('Z', ''))
                    else:
                        last_updated_dt = last_updated

                    # No timezone conversion — both are naive local time
                    time_diff = (current_time - last_updated_dt).total_seconds()
                    new_status = "online" if time_diff <= threshold_seconds else "offline"
                    current_status = connection.get('status')

                    if current_status != new_status:
                        Device.objects(id=device.id).update_one(
                            set__connection={"last_updated": last_updated, "status": new_status}
                        )
                        updates_count += 1
                        logger.info(f"[GATEWAY] Device {device.device_id} status updated to {new_status} (last_updated: {time_diff:.0f}s ago)")

                except Exception as e:
                    logger.error(f"[GATEWAY] Error checking status for device {device.device_id}: {str(e)}")
                    continue

            if updates_count > 0:
                logger.info(f"[GATEWAY] Device status check completed. Updated {updates_count} devices.")

        except Exception as e:
            logger.error(f"[GATEWAY] Error in check_and_update_device_status: {str(e)}")
    
    
    @classmethod
    def send_heartbeat(cls):
        """
        Send device status heartbeat to charging API using data from database.
        Runs every 2 minutes to report device online/offline status.
        Payload format:
        {
            "devices": [
                {"id": "15", "online": true, "last_seen": "2026-04-05T20:55:58+00:00"},
                {"id": "16", "online": true, "last_seen": "2026-04-05T20:55:58+00:00"}
            ]
        }
        """
        try:
            from esp32OTA.config import config
            
            devices_payload = []
            
            # Get all devices with client_id and their status from DB
            devices = Device.objects(client_id__ne=None).only(
                'client_id', 'connection', 'device_id'
            )
            
            for device in devices:
                try:
                    connection = device.connection or {}
                    status = connection.get('status', 'offline')
                    last_updated = connection.get('last_updated')
                    
                    if not last_updated:
                        logger.debug(f"[HEARTBEAT] Device {device.device_id} has no last_updated")
                        continue
                    
                    is_online = (status == 'online')
                    
                    devices_payload.append({
                        "id": str(device.client_id),
                        "online": is_online,
                        "last_seen": last_updated
                    })
                    
                except Exception as e:
                    logger.warning(f"[HEARTBEAT] Error processing device {device.device_id}: {e}")
                    continue
            
            # Send heartbeat payload to API
            if devices_payload:
                payload = {"devices": devices_payload}
                
                base_url = getattr(config, 'ORKOFLEET_BASE_URL')
                api_url = f"{base_url}/api/v1/charging/heartbeat"
                headers = {"Content-Type": "application/json"}
                
                logger.info(f"[HEARTBEAT] Sending payload: {json.dumps(payload)}")
                
                response = requests.post(api_url, json=payload, headers=headers, timeout=10)
                
                logger.info(f"[HEARTBEAT] Response status: {response.status_code}")
                
                if response.status_code == 200:
                    logger.info(f"[HEARTBEAT] Successfully sent heartbeat for {len(devices_payload)} devices")
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] [HEARTBEAT] Sent heartbeat for {len(devices_payload)} devices")
                else:
                    logger.warning(f"[HEARTBEAT] API returned status {response.status_code}: {response.text}")
            else:
                logger.info("[HEARTBEAT] No devices with client_id to send heartbeat")
                
        except Exception as e:
            logger.error(f"[HEARTBEAT] Error in send_heartbeat: {str(e)}")
