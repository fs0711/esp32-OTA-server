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
    def update_device_last_updated(cls, device_id, timestamp):
        """
        Updates the device's last_updated field in the connection object.
        Called after successfully posting device status to OrkoFleet API.
        """
        try:
            # Query device by device_id
            device = Device.objects(device_id=str(device_id)).first()
            
            # Fallback: iterate through devices if direct query fails
            if not device:
                for d in Device.objects.only('device_id', 'connection'):
                    if str(d.device_id) == str(device_id):
                        device = d
                        break
            
            if not device:
                logger.warning(f"[GATEWAY] Device {device_id} not found for updating last_updated")
                return False
            
            # Update connection.last_updated with the timestamp
            if not device.connection:
                device.connection = {}
            
            device.connection['last_updated'] = timestamp
            device.save()
            
            logger.info(f"[GATEWAY] Updated {device_id} last_updated to {timestamp}")
            return True
            
        except Exception as e:
            logger.error(f"[GATEWAY] Error updating last_updated for {device_id}: {str(e)}")
            return False

    @classmethod
    def check_and_update_device_status(cls):
        """
        Checks all devices' last_updated timestamps and updates their status to online/offline.
        If last_updated is within 2 minutes: status = online
        If last_updated is more than 2 minutes ago: status = offline
        """
        try:
            from datetime import datetime, timezone
            
            # Get current time
            current_time = datetime.now(timezone.utc)
            threshold_seconds = 120  # 2 minutes
            
            # Get all devices from database
            devices = Device.objects()
            
            if not devices:
                return
            
            updates_count = 0
            
            for device in devices:
                try:
                    # Get last_updated from connection object
                    connection = getattr(device, 'connection', {})
                    if not connection:
                        continue
                    
                    last_updated = connection.get('last_updated')
                    if not last_updated:
                        continue
                    
                    # Parse last_updated timestamp
                    # Handle both string and datetime formats
                    if isinstance(last_updated, str):
                        # Try to parse ISO format timestamp
                        try:
                            last_updated_dt = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
                        except:
                            # Try other formats
                            last_updated_dt = datetime.fromisoformat(last_updated)
                    else:
                        last_updated_dt = last_updated
                    
                    # Make sure both are timezone-aware for comparison
                    if last_updated_dt.tzinfo is None:
                        last_updated_dt = last_updated_dt.replace(tzinfo=timezone.utc)
                    
                    # Calculate time difference
                    time_diff = (current_time - last_updated_dt).total_seconds()
                    
                    # Determine status
                    new_status = "online" if time_diff <= threshold_seconds else "offline"
                    
                    # Get current status
                    current_status = connection.get('status')
                    
                    # Update if status changed
                    if current_status != new_status:
                        device.connection['status'] = new_status
                        device.save()
                        updates_count += 1
                        logger.info(f"[GATEWAY] Device {device.device_id} status updated to {new_status} (last_updated: {time_diff}s ago)")
                    
                except Exception as e:
                    logger.error(f"[GATEWAY] Error checking status for device {device.device_id}: {str(e)}")
                    continue
            
            if updates_count > 0:
                logger.info(f"[GATEWAY] Device status check completed. Updated {updates_count} devices.")
            
        except Exception as e:
            logger.error(f"[GATEWAY] Error in check_and_update_device_status: {str(e)}")

    @classmethod
    def refresh_all_devices_online(cls):
        """
        Refreshes all devices by updating their last_updated to current time and status to online.
        Called every 90 seconds to keep device connection status current.
        """
        try:
            from datetime import datetime, timezone
            
            # Get current time
            current_time = datetime.now(timezone.utc)
            
            # Get all devices from database
            devices = Device.objects()
            
            if not devices:
                return
            
            updates_count = 0
            
            for device in devices:
                try:
                    # Initialize or update connection object
                    if not device.connection:
                        device.connection = {}
                    
                    # Update last_updated to current time
                    device.connection['last_updated'] = current_time
                    # Set status to online
                    device.connection['status'] = 'online'
                    device.save()
                    updates_count += 1
                    
                except Exception as e:
                    logger.error(f"[GATEWAY] Error refreshing device {device.device_id}: {str(e)}")
                    continue
            
            logger.info(f"[GATEWAY] Refreshed {updates_count} devices - set all to online with current timestamp")
            
        except Exception as e:
            logger.error(f"[GATEWAY] Error in refresh_all_devices_online: {str(e)}")

    @classmethod
    def poll_devices(cls):
        """
        Loads all active devices, fetches status from external API using client_id,
        and publishes the data back to MQTT.
        """
        # 1. Ensure MQTT service is started
        if not mqtt_service.client.is_connected():
            try:
                mqtt_service.start()
            except:
                pass
        
        client = mqtt_service.client
        if not client.is_connected():
            return

        # Fetch only active devices from the database
        active_devices = Device.objects(status=constants.OBJECT_STATUS_ACTIVE)
        
        if not active_devices:
            return

        for device in active_devices:
            # 1. Get client_id from device object
            client_id = getattr(device, 'client_id', None)
            
            # Fallback check if it's in the connection dict
            if not client_id:
                connection_data = getattr(device, 'connection', {})
                if isinstance(connection_data, dict):
                    client_id = connection_data.get('client_id')
            
            if not client_id:
                continue

            try:
                # 2. Fetch data from external API
                from esp32OTA.config import config
                base_url = getattr(config, 'ORKOFLEET_BASE_URL')
                api_url = f"{base_url}/api/v2/power-sockets/status/{client_id}"
                
                response = requests.get(api_url, timeout=0.8) # Tight timeout for 1s loop
                
                if response.status_code == 200:
                    api_data = response.json()
                    
                    # 3. Process data for command payload
                    current_time = datetime.now()
                    
                    # Filter 's' array to remove 'box_open_request' and shorten keys
                    raw_s = api_data.get('s', [])
                    filtered_s = []
                    for item in raw_s:
                        # Shorten variable names as requested:
                        # status -> st, session_id -> sid, credit -> cr
                        filtered_item = {}
                        if 'status' in item:
                            filtered_item['st'] = item['status']
                        if 'session_id' in item:
                            filtered_item['sid'] = item['session_id']
                        if 'credit' in item:
                            filtered_item['cr'] = item['credit']
                        
                        # Preserve other keys if any, except box_open_request
                        for k, v in item.items():
                            if k not in ['status', 'session_id', 'credit', 'box_open_request']:
                                filtered_item[k] = v
                                
                        filtered_s.append(filtered_item)

                    # Check if status has changed before publishing
                    # We use device.device_id as the key to track state
                    status_changed = True
                    current_status_summary = json.dumps(filtered_s, sort_keys=True)
                    if cls._last_status.get(str(device.device_id)) == current_status_summary:
                        status_changed = False
                    
                    if status_changed:
                        topic = f"ZV/DEVICES/{device.device_id}/command"
                        
                        # Optimized payload as per user request: timestamp -> t
                        payload = json.dumps({
                            "t": int(current_time.timestamp()), # Unix Epoch
                            "s": filtered_s
                        })
                        
                        # Using retain=True so the latest command is always available to the device
                        client.publish(topic, payload, qos=1, retain=True)
                        cls._last_status[str(device.device_id)] = current_status_summary
                        print(f"[{current_time.strftime('%H:%M:%S')}] [GW] -> {device.device_id} | Topic: {topic}")
                        print(f"[{current_time.strftime('%H:%M:%S')}] [GW] Payload: {payload}")
                    else:
                        # Skip publishing if nothing changed
                        pass
                else:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] [GATEWAY] ERR {client_id}: {response.status_code}")
                    logger.error(f"[GATEWAY] API Error for {client_id}: {response.status_code}")
                    
            except Exception as e:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] [GATEWAY] ERR {device.device_id}: {str(e)[:50]}")
                logger.error(f"[GATEWAY] Error processing {device.device_id}: {str(e)}")


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
