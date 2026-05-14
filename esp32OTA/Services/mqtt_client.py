import paho.mqtt.client as mqtt
import logging
import json
import threading
import requests
from datetime import datetime
from esp32OTA.config import config
from esp32OTA.DeviceManagement.models.Device import Device
from esp32OTA.generic.services.utils import common_utils, constants

logger = logging.getLogger(__name__)

class MQTTClientService:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(MQTTClientService, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
            
        self.client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
        
        self.broker_host = getattr(config, 'MQTT_BROKER_HOST')
        self.broker_port = getattr(config, 'MQTT_BROKER_PORT')
        
        self.broker_stats = {}
        self.device_data = {}
        self.last_timestamps = {}  # Track last timestamp per device
        self.last_usage_timestamps = {} # Track last usage timestamp per device
        self._initialized = True

    def on_connect(self, client, userdata, flags, reason_code, properties=None):
        if reason_code == 0:
            logger.info("[MQTT] Connected successfully")
            # Subscribe to stats and device topics
            client.subscribe("$SYS/broker/#", qos=1)
            client.subscribe("ZV/DEVICES/+/status/#", qos=1)
            client.subscribe("ZV/DEVICES/+/usage/#", qos=1)
            client.subscribe("ZV/DEVICES/+/command", qos=1)
            client.subscribe("ZV/DEVICES/+/send_config", qos=1)
        else:
            logger.error(f"[MQTT] Connection failed with code {reason_code}")

    def on_message(self, client, userdata, message):
        try:
            topic = message.topic
            payload_str = message.payload.decode()
            
            if topic.startswith("$SYS/broker/"):
                stat_key = topic.replace("$SYS/broker/", "")
                self.broker_stats[stat_key] = payload_str
            elif topic.startswith("ZV/DEVICES/"):
                # Handle incoming status from devices
                # Expected topic format: ZV/DEVICES/DV-2/status
                topic_parts = topic.split('/')
                if len(topic_parts) >= 3 and "status" in topic:
                    device_id = topic_parts[2]
                    try:
                        data = json.loads(payload_str)
                        # Identify if this is a new message by timestamp (t) BEFORE logging
                        new_timestamp = data.get("t") or data.get("timestamp")
                        if new_timestamp is not None:
                            last_ts = self.last_timestamps.get(device_id)
                            if last_ts == new_timestamp:
                                # Duplicate - silent ignore or debug log only
                                return
                        
                        # Only log if it's unique/new
                        logger.info(f"[MQTT] Unique status for {device_id}: {payload_str}")
                        self.handle_device_status(device_id, data)
                    except json.JSONDecodeError:
                        logger.error(f"[MQTT] Failed to decode status payload for {device_id}")
                elif len(topic_parts) >= 3 and "usage" in topic:
                    device_id = topic_parts[2]
                    try:
                        data = json.loads(payload_str)
                        new_timestamp = data.get("t") or data.get("timestamp")
                        if new_timestamp is not None:
                            if self.last_usage_timestamps.get(device_id) == new_timestamp:
                                return
                        
                        logger.info(f"[MQTT] Unique usage for {device_id}: {payload_str}")
                        self.handle_device_usage(device_id, data)
                    except json.JSONDecodeError:
                        logger.error(f"[MQTT] Failed to decode usage payload for {device_id}")
                
                # Check for config request (send_config = 1)
                if len(topic_parts) >= 3:
                    device_id = topic_parts[2]
                    try:
                        data = json.loads(payload_str)
                        if data.get("send_config") == 1:
                            logger.info(f"[MQTT] Config request received from {device_id}")
                            self.handle_config_request(device_id)
                    except (json.JSONDecodeError, TypeError):
                        pass  # Not JSON or no send_config flag
                
                # Handle command topic
                if len(topic_parts) >= 3 and "command" in topic:
                    device_id = topic_parts[2]
                    logger.info(f"[MQTT] Command received from {device_id}: {payload_str}")
                    self.handle_config_request(device_id)
                
                # Handle send_config topic
                if len(topic_parts) >= 3 and "send_config" in topic:
                    device_id = topic_parts[2]
                    try:
                        # Try to parse as JSON, but also handle plain "1" or "1\n"
                        try:
                            data = json.loads(payload_str)
                            if data == 1 or data.get("send_config") == 1:
                                logger.info(f"[MQTT] Config request received from {device_id}")
                                self.handle_config_request(device_id)
                        except (json.JSONDecodeError, TypeError):
                            # Handle as plain text/number
                            if payload_str.strip() == "1":
                                logger.info(f"[MQTT] Config request received from {device_id}")
                                self.handle_config_request(device_id)
                    except Exception as e:
                        logger.error(f"[MQTT] Error handling send_config from {device_id}: {str(e)}")
        except Exception as e:
            logger.error(f"[MQTT] Error in on_message: {str(e)}")

    def handle_device_status(self, device_id, raw_data):
        """
        Processes incoming device status, finds client_id (c_s_id),
        checks for duplicate timestamps, and forwards to the external status API.
        """
        try:
            # 0. Deduplicate by timestamp (t)
            new_timestamp = raw_data.get("t") or raw_data.get("timestamp")
            if new_timestamp is not None:
                # Update local cache (Already checked uniqueness in on_message)
                self.last_timestamps[device_id] = new_timestamp

            # 1. Look up device in database to get client_id
            # Step 1: Query by device_id (string)
            device = Device.objects(device_id=str(device_id)).first()
            
            # Step 2: Fallback - SequenceFields can be tricky with string lookups in some versions
            if not device:
                for d in Device.objects.only('device_id', 'client_id', 'connection'):
                    if str(d.device_id) == str(device_id):
                        device = d
                        break

            # --- LOOKUP LOGIC ---
            if not device:
                return # Silently stop if device not in DB
            else:
                # Get the client_id (OrkoFleet's c_s_id)
                device[constants.DEVICE__CONNECTION] = {"last_updated": new_timestamp,
                                                        "status":device[constants.DEVICE__CONNECTION].get("status")}
                device.save()
                client_id = getattr(device, 'client_id', None)
                if not client_id:
                    connection_data = getattr(device, 'connection', {})
                    if isinstance(connection_data, dict):
                        client_id = connection_data.get('client_id')
            
            if not client_id:
                return


            # 2. Map incoming status format to requested API format
            # Device sends: {"t": 123, "s": [{"id": 2, "st": 0, "sg": "w", "e": ["E2"]}], "e": []}
            incoming_s = raw_data.get("s", [])
            mapped_s = []
            
            for item in incoming_s:
                # Signal type mapping: w -> wifi, g -> gsm
                signal_raw = item.get("sg")
                signal_mapped = signal_raw
                if signal_raw == "w":
                    signal_mapped = "wifi"
                elif signal_raw == "g":
                    signal_mapped = "gsm"

                mapped_s.append({
                    "id": item.get("id"),
                    "status": item.get("st"), # st -> status
                    "signal_type": signal_mapped,
                    "e": item.get("e", [])
                })
            
            # Root error field: send to OrkoFleet only if it has values
            root_errors = raw_data.get("e", [])
            
            payload = {
                "c_s_id": int(client_id) if str(client_id).isdigit() else client_id,
                "s": mapped_s,
                "e": root_errors
            }

            # 3. Post to API
            base_url = getattr(config, 'ORKOFLEET_BASE_URL')
            api_url = f"{base_url}/api/v2/power-sockets/status"
            headers = {
                "Content-Type": "application/json"
            }
            
            # Always log to terminal
            logger.info(f"[MQTT] -> API Payload: {json.dumps(payload)}")
            
            # Save to database log ONLY if 'e' has values
            has_errors = any(item.get("e") for item in mapped_s) or bool(root_errors)
            if has_errors:
                from esp32OTA.GatewayLogging.controllers.GatewayLoggingController import GatewayLoggingController
                from esp32OTA import app
                with app.app_context():
                    GatewayLoggingController.log_gateway_activity(json.dumps(payload), "sent")

            response = requests.post(api_url, json=payload, headers=headers, timeout=5)
            logger.info(f"[MQTT] Forwarded {device_id} status to API. Status: {response.status_code}")
            
            # Update device's last_updated timestamp after successful API post
            if response.status_code == 200 and new_timestamp is not None:
                from esp32OTA.Services.GatewayService import GatewayService
                GatewayService.update_device_last_updated(device_id, new_timestamp)
            
            # Restore terminal logging of response (but not database)
            try:
                resp_data = response.json()
                logger.info(f"[MQTT] API Response: {json.dumps(resp_data)}")
            except:
                logger.info(f"[MQTT] API Response: {response.text}")
            
        except Exception as e:
            logger.error(f"[MQTT] Error handling device status for {device_id}: {str(e)}")

    def handle_device_usage(self, device_id, raw_data):
        """
        Processes incoming device usage, maps fields, and posts to the usage API.
        """
        try:
            new_timestamp = raw_data.get("t") or raw_data.get("timestamp")
            if new_timestamp:
                self.last_usage_timestamps[device_id] = new_timestamp

            usage_inner = raw_data.get("d", {})
            if not usage_inner:
                return

            # Map fields: s->socket_id, se->session_id, co->consumption, cu->current, v->voltage, d->duration, is->is_completed
            payload = {
                "socket_id": usage_inner.get("s"),
                "session_id": usage_inner.get("se"),
                "consumption": usage_inner.get("co"),
                "current": usage_inner.get("cu"),
                "voltage": usage_inner.get("v"),
                "duration": usage_inner.get("d"),
                "is_completed": usage_inner.get("is")
            }

            base_url = getattr(config, 'ORKOFLEET_BASE_URL')
            api_url = f"{base_url}/api/v2/charge-sessions/add-usage-data"
            headers = {"Content-Type": "application/json"}
            
            # Always log outgoing to terminal
            logger.info(f"[MQTT] -> Usage API Payload: {json.dumps(payload)}")
            
            response = requests.post(api_url, json=payload, headers=headers, timeout=5)
            logger.info(f"[MQTT] Forwarded {device_id} usage to API. Status: {response.status_code}")
            
            # Restore terminal logging of response (but not database)
            try:
                resp_data = response.json()
                logger.info(f"[MQTT] Usage API Response: {json.dumps(resp_data)}")
            except:
                logger.info(f"[MQTT] Usage API Response: {response.text}")

        except Exception as e:
            logger.error(f"[MQTT] Error handling device usage for {device_id}: {str(e)}")

    def handle_config_request(self, device_id):
        """
        Handles config request from device (send_config = 1).
        Fetches device config and publishes shortened variables and QR code to config_update topic.
        """
        try:
            # Fetch device from database
            device = Device.objects(device_id=str(device_id)).first()
            
            if not device:
                # Fallback - try iterating through devices
                for d in Device.objects.only('device_id', 'variables', 'qr_code'):
                    if str(d.device_id) == str(device_id):
                        device = d
                        break
            
            if not device:
                logger.warning(f"[MQTT] Device {device_id} not found in database for config request")
                return
            
            # Shorten variable names
            var_mapping = {
                "CT_CAL_HIGH": "cc_h",
                "CT_CAL_LOW": "cc_l",
                "CT_CAL_MID": "cc_m",
                "CT_MAX_CURRENT": "cmc",
                "VCAL": "vc",
                "app": "app",
                "app_password": "app_pwd",
                "app_user": "app_usr",
                "base_url": "burl",
                "bt_mac": "bt_m",
                "config_timeout": "cfg_to",
                "cut_A": "cut_a",
                "device_id": "did",
                "ime1": "ime1",
                "ping_api": "ping",
                "status_api": "status",
                "sw_timeout": "sw_to",
                "update_data_api": "update",
                "wifi_mac": "wifi_m",
                "wifi_password": "wifi_pwd",
                "wifi_ssid": "wifi_ssid"
            }
            
            shortened_variables = {}
            for key, value in device.variables.items():
                short_key = var_mapping.get(key, key)
                shortened_variables[short_key] = value
            
            # Build config update payload
            topic = f"ZV/DEVICES/{device.device_id}/config_update"
            payload = {
                "t": int(datetime.now().timestamp()),
                "variables": shortened_variables,
                "qr_code": device.qr_code
            }
            
            # Publish to MQTT
            self.publish(topic, payload)
            logger.info(f"[MQTT] Config sent to {device_id}")
            
        except Exception as e:
            logger.error(f"[MQTT] Error handling config request for {device_id}: {str(e)}")

    def on_disconnect(self, client, userdata, disconnect_flags, reason_code, properties=None):
        logger.warning(f"[MQTT] Disconnected: {reason_code}")

    def start(self):
        try:
            self.client.connect(self.broker_host, self.broker_port, 60)
            self.client.loop_start()
            logger.info(f"[MQTT] Started loop for {self.broker_host}")
        except Exception as e:
            logger.error(f"[MQTT] Failed to start: {str(e)}")

    def stop(self):
        self.client.loop_stop()
        self.client.disconnect()

    def publish_firmware_update(self, device_id, firmware_data):
        """
        Publishes firmware update information to the device's firmware topic.
        """
        topic = f"ZV/DEVICES/{device_id}/firmware"
        try:
            payload = json.dumps(firmware_data)
            self.client.publish(topic, payload, qos=1)
            logger.info(f"[MQTT] Published firmware update to {topic}: {payload}")
        except Exception as e:
            logger.error(f"[MQTT] Failed to publish firmware update to {topic}: {str(e)}")

    def publish(self, topic, message, qos=1):
        """
        Publishes a message to a specific topic.
        """
        try:
            if isinstance(message, (dict, list)):
                payload = json.dumps(message)
            else:
                payload = str(message)

            self.client.publish(topic, payload, qos=qos)
            logger.info(f"[MQTT] Published to {topic}: {payload}")
            return True
        except Exception as e:
            logger.error(f"[MQTT] Failed to publish to {topic}: {str(e)}")
            return False

mqtt_service = MQTTClientService()
