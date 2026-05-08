import time
import logging
import requests
import json
import os
import subprocess
from datetime import datetime
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
    def send_heartbeat(cls):
        """
        Gathers online/offline status of all devices using c_s_id as the ID.
        Compares device timestamp against current time:
        - If difference > 2 minutes: offline
        - If difference <= 2 minutes: online
        Sends a POST request to the heartbeat API.
        """
        heartbeat_data = []
        
        # Proactively check DB to ensure all devices are reported
        try:
            from esp32OTA.generic.services.utils import common_utils
            current_time = datetime.now().timestamp()  # Current time in Unix epoch
            db_devices = Device.objects.only('device_id', 'client_id', 'connection')
            
            for dev in db_devices:
                d_id = str(dev.device_id)
                c_s_id = getattr(dev, 'client_id', None)
                if not c_s_id:
                    c_s_id = dev.connection.get('client_id') if isinstance(dev.connection, dict) else d_id
                
                # Skip devices with null/None IDs
                if c_s_id is None:
                    continue
                
                info = cls._last_data.get(d_id, {})
                device_timestamp = info.get("timestamp")  # Device's timestamp from MQTT
                
                # Determine online/offline status based on timestamp difference
                online_status = True  # Default to online
                last_seen_iso = info.get("last_seen", common_utils.get_time_iso())
                
                if device_timestamp is not None:
                    # Calculate difference in seconds
                    time_diff = current_time - device_timestamp
                    # If difference > 120 seconds (2 minutes), mark offline
                    if time_diff > 120:
                        online_status = False
                    else:
                        online_status = True
                    
                    # Convert device timestamp to ISO format for last_seen
                    try:
                        last_seen_iso = datetime.fromtimestamp(device_timestamp).isoformat()
                    except:
                        last_seen_iso = common_utils.get_time_iso()

                heartbeat_data.append({
                    "id": c_s_id,
                    "online": online_status, # Default to true if in DB
                    "last_seen": last_seen_iso
                })

                # Update _last_data with online/offline status for dashboard
                if d_id not in cls._last_data:
                    # Create entry if device never sent MQTT message
                    cls._last_data[d_id] = {
                        "id": d_id,
                        "c_s_id": c_s_id
                    }
                
                cls._last_data[d_id].update({
                    "online": online_status,
                    "last_seen": last_seen_iso,
                    "timestamp": current_time  # Update timestamp to now
                })

                # Update Device connection status in DB
                try:
                    status_str = "online" if online_status else "offline"
                    # User requested ISO for server, but DB display was MM-DD-YYYY HH:MM:SS
                    formatted_last_seen = datetime.now().strftime("%m-%d-%Y %H:%M:%S")
                    
                    dev.update(set__connection__status=status_str, set__connection__last_update=formatted_last_seen)
                except Exception as update_err:
                    logger.error(f"[HB] Error updating device {d_id} in DB: {update_err}")
        except Exception as db_err:
            logger.error(f"[HB] DB Error: {db_err}")
            # Fallback to dictionary - use same timestamp-based logic
            from esp32OTA.generic.services.utils import common_utils
            current_time = datetime.now().timestamp()
            for device_id, info in cls._last_data.items():
                c_s_id = info.get("c_s_id", device_id)
                # Skip devices with null/None IDs
                if c_s_id is None:
                    continue
                
                device_timestamp = info.get("timestamp")
                online_status = True  # Default to online
                last_seen_iso = info.get("last_seen", common_utils.get_time_iso())
                
                if device_timestamp is not None:
                    time_diff = current_time - device_timestamp
                    online_status = time_diff <= 120  # True if within 2 minutes
                    try:
                        last_seen_iso = datetime.fromtimestamp(device_timestamp).isoformat()
                    except:
                        last_seen_iso = common_utils.get_time_iso()
                
                heartbeat_data.append({
                    "id": c_s_id,
                    "online": online_status,
                    "last_seen": last_seen_iso
                })
                
                # Update _last_data with online/offline status for dashboard
                if device_id not in cls._last_data:
                    # Create entry if device never sent MQTT message
                    cls._last_data[device_id] = {
                        "id": device_id,
                        "c_s_id": c_s_id
                    }
                
                cls._last_data[device_id].update({
                    "online": online_status,
                    "last_seen": last_seen_iso,
                    "timestamp": current_time  # Update timestamp to now
                })

        if not heartbeat_data:
            return

        try:
            from esp32OTA.config import config
            base_url = getattr(config, 'ORKOFLEET_BASE_URL')
            url = f"{base_url}/api/v1/charging/heartbeat"
            payload = {"devices": heartbeat_data}
            headers = {
                "Content-Type": "application/json"
            }
            
            # Log the outgoing heartbeat payload
            print(f"[{datetime.now().strftime('%H:%M:%S')}] [HB] Payload: {json.dumps(payload, indent=2)}")
            
            response = requests.post(url, json=payload, headers=headers, timeout=5)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] [HB] Sent status for {len(heartbeat_data)} devices. Status: {response.status_code}")
            try:
                resp_json = response.json()
                print(f"[{datetime.now().strftime('%H:%M:%S')}] [HB] Response: {json.dumps(resp_json, indent=2)}")
            except:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] [HB] Response: {response.text}")
        except Exception as e:
            logger.error(f"[HB] Error sending heartbeat: {str(e)}")

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
                    
                    # Update local state for dashboard
                    cls._last_data[device.device_id] = {
                        "id": device.device_id,
                        "c_s_id": str(api_data.get('c_s_id', device.device_id)),
                        "payloads": {
                            "status": api_data,
                            "usage": cls._last_data.get(device.device_id, {}).get("payloads", {}).get("usage", {})
                        },
                        "timestamp": int(current_time.timestamp()),  # Store epoch timestamp for heartbeat check
                        "last_seen": current_time.isoformat()
                    }
                else:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] [GATEWAY] ERR {client_id}: {response.status_code}")
                    logger.error(f"[GATEWAY] API Error for {client_id}: {response.status_code}")
                    
            except Exception as e:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] [GATEWAY] ERR {device.device_id}: {str(e)[:50]}")
                logger.error(f"[GATEWAY] Error processing {device.device_id}: {str(e)}")
