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
    _max_logs = 100
    _last_heartbeat_time = 0

    @classmethod
    def send_heartbeat(cls):
        """
        Gathers online/offline status of all devices using c_s_id as the ID,
        and sends a POST request to the heartbeat API.
        """
        heartbeat_data = []
        
        # Proactively check DB to ensure all devices are reported
        try:
            db_devices = Device.objects.only('device_id', 'client_id', 'connection')
            for dev in db_devices:
                d_id = str(dev.device_id)
                c_s_id = getattr(dev, 'client_id', None)
                if not c_s_id:
                    c_s_id = dev.connection.get('client_id') if isinstance(dev.connection, dict) else d_id
                
                info = cls._last_data.get(d_id, {})
                heartbeat_data.append({
                    "id": c_s_id,
                    "online": info.get("online", True), # Default to true if in DB
                    "last_seen": info.get("last_seen", datetime.now().isoformat())
                })
        except Exception as db_err:
            logger.error(f"[HB] DB Error: {db_err}")
            # Fallback to dictionary
            for device_id, info in cls._last_data.items():
                heartbeat_data.append({
                    "id": info.get("c_s_id", device_id),
                    "online": info.get("online", False),
                    "last_seen": info.get("last_seen")
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
        # 1. Heartbeat logic (every 15 seconds)
        now_ts = time.time()
        if now_ts - cls._last_heartbeat_time >= 15:
            cls.send_heartbeat()
            cls._last_heartbeat_time = now_ts

        # 2. Ensure MQTT service is started
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
                    
                    # Filter 's' array to remove 'box_open_request'
                    raw_s = api_data.get('s', [])
                    filtered_s = []
                    for item in raw_s:
                        filtered_item = {k: v for k, v in item.items() if k != 'box_open_request'}
                        filtered_s.append(filtered_item)

                    topic = f"devices/{device.device_id}/command"
                    
                    # Optimized payload as per user request
                    payload = json.dumps({
                        "timestamp": int(current_time.timestamp()), # Unix Epoch
                        "s": filtered_s
                    })
                    
                    # Using retain=True so the latest command is always available to the device
                    client.publish(topic, payload, retain=True)
                    print(f"[{current_time.strftime('%H:%M:%S')}] [GW] -> {device.device_id} | Topic: {topic}")
                    print(f"[{current_time.strftime('%H:%M:%S')}] [GW] Payload: {payload}")
                    
                    # Update local state for dashboard
                    cls._last_data[device.device_id] = {
                        "id": device.device_id,
                        "c_s_id": str(api_data.get('c_s_id', device.device_id)),
                        "payloads": {
                            "status": api_data,
                            "usage": cls._last_data.get(device.device_id, {}).get("payloads", {}).get("usage", {})
                        },
                        "online": True,
                        "last_seen": current_time.isoformat()
                    }
                else:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] [GATEWAY] ERR {client_id}: {response.status_code}")
                    if device.device_id in cls._last_data:
                        cls._last_data[device.device_id]["online"] = False
                    logger.error(f"[GATEWAY] API Error for {client_id}: {response.status_code}")
                    
            except Exception as e:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] [GATEWAY] ERR {device.device_id}: {str(e)[:50]}")
                if device.device_id in cls._last_data:
                    cls._last_data[device.device_id]["online"] = False
                logger.error(f"[GATEWAY] Error processing {device.device_id}: {str(e)}")
