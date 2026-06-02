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
        self.last_config_request_time = {}  # Track last config request time per device
        self.last_incomplete_usage = {}  # Track last usage payload per device for stale-completion watchdog
        self.connected = False  # Track connection state
        self._initialized = True

    def on_connect(self, client, userdata, flags, reason_code, properties=None):
        if reason_code == 0:
            self.connected = True
            logger.info("[MQTT] Connected successfully")
            # Subscribe to stats and device topics
            client.subscribe("$SYS/broker/#", qos=1)
            client.subscribe("ZV/DEVICES/+/status/#", qos=1)
            client.subscribe("ZV/DEVICES/+/usage/#", qos=1)
            client.subscribe("ZV/DEVICES/+/command", qos=1)
            client.subscribe("ZV/DEVICES/+/send_config", qos=1)
            client.subscribe("ZV/DEVICES/+/configuration", qos=1)
            client.subscribe("ZV/DEVICES/+/setconfig", qos=1)
        else:
            self.connected = False
            logger.error(f"[MQTT] Connection failed with code {reason_code}")

    def on_message(self, client, userdata, message):
        try:
            topic = message.topic
            payload_str = message.payload.decode()
            
            if topic.startswith("$SYS/broker/"):
                stat_key = topic.replace("$SYS/broker/", "")
                self.broker_stats[stat_key] = payload_str
            elif topic.startswith("ZV/DEVICES/"):
                logger.info(f"[MQTT] <<< RECEIVED | topic: '{topic}' | payload: '{payload_str}'")
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
                
                # Check for config request (send_config = 1) in JSON payload
                if len(topic_parts) >= 3:
                    device_id = topic_parts[2]
                    try:
                        data = json.loads(payload_str)
                        if isinstance(data, dict) and data.get("send_config") == 1:
                            logger.info(f"[MQTT] Config request received from {device_id}")
                            self.handle_config_request(device_id)
                    except (json.JSONDecodeError, TypeError):
                        pass  # Not JSON or no send_config flag
                
                # Handle configuration topic
                if len(topic_parts) >= 3 and topic_parts[3] == "configuration":
                    device_id = topic_parts[2]
                    logger.info(f"[MQTT] Configuration request received from {device_id}, payload: {payload_str}")
                    self.handle_config_request(device_id)

                # Handle setconfig topic
                if len(topic_parts) >= 4 and topic_parts[3] == "setconfig":
                    device_id = topic_parts[2]
                    try:
                        data = json.loads(payload_str)
                        logger.info(f"[MQTT] setconfig received from {device_id}: {payload_str}")
                        self.handle_setconfig(device_id, data)
                    except json.JSONDecodeError:
                        logger.error(f"[MQTT] Failed to decode setconfig payload for {device_id}")
        except Exception as e:
            logger.error(f"[MQTT] Error in on_message: {str(e)}")

    def handle_device_status(self, device_id, raw_data):
        """
        Processes incoming device status, finds client_id (c_s_id),
        and forwards to the external status API.
        """
        try:
            # 1. Look up device in database to get client_id
            device = Device.objects(device_id=str(device_id)).first()

            if not device:
                for d in Device.objects.only('device_id', 'client_id', 'connection'):
                    if str(d.device_id) == str(device_id):
                        device = d
                        break

            if not device:
                return

            server_timestamp = common_utils.get_time_iso()
            last_updated = common_utils.epoch_to_datetime(server_timestamp * 1000)
            Device.objects(id=device.id).update_one(
                **{f"set__{constants.DEVICE__CONNECTION}": {"last_updated": last_updated, "status": "online"}}
            )

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
            
            logger.info(f"[MQTT] -> API Payload: {json.dumps(payload)}")

            # Save to database log ONLY if 'e' contains actual error values (not empty or [0] or 0)
            has_errors = any(item.get("e") and item.get("e") != 0 and item.get("e") != [0] for item in mapped_s) or \
                         (root_errors and root_errors != 0 and root_errors != [0])
            if has_errors:
                from esp32OTA.GatewayLogging.controllers.GatewayLoggingController import GatewayLoggingController
                from esp32OTA import app
                with app.app_context():
                    GatewayLoggingController.log_gateway_activity(json.dumps(payload), "sent")

            response = requests.post(api_url, json=payload, headers=headers, timeout=5)
            logger.info(f"[MQTT] Forwarded {device_id} status to API. Status: {response.status_code}")
            
            try:
                resp_data = response.json()
                logger.info(f"[MQTT] API Response: {json.dumps(resp_data)}")
            except:
                logger.info(f"[MQTT] API Response: {response.text}")
            
        except Exception as e:
            logger.error(f"[MQTT] Error handling device status for {device_id}: {str(e)}", exc_info=True)

    def handle_device_usage(self, device_id, raw_data):
        """
        Processes incoming device usage, maps fields, and posts to the usage API.
        """
        try:
            new_timestamp = raw_data.get("t") or raw_data.get("timestamp")

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

            # Save to UsageLogging before sending to API
            try:
                from esp32OTA.UsageLogging.controllers.UsageLoggingController import UsageLoggingController
                from esp32OTA import app
                
                usage_log_data = {
                    constants.USAGE_LOGGING__DEVICE_ID: str(device_id),
                    constants.USAGE_LOGGING__TIMESTAMP: str(common_utils.get_time_iso()),
                    constants.USAGE_LOGGING__SOCKET_ID: payload["socket_id"],
                    constants.USAGE_LOGGING__SESSION_ID: str(payload["session_id"]),
                    constants.USAGE_LOGGING__CONSUMPTION: payload["consumption"],
                    constants.USAGE_LOGGING__CURRENT: payload["current"],
                    constants.USAGE_LOGGING__VOLTAGE: payload["voltage"],
                    constants.USAGE_LOGGING__DURATION: payload["duration"],
                    constants.USAGE_LOGGING__IS_COMPLETED: payload["is_completed"]
                }
                
                with app.app_context():
                    UsageLoggingController.log_usage(data=usage_log_data)
                    logger.info(f"[MQTT] Usage data saved to database for {device_id}")
            except Exception as log_err:
                logger.error(f"[MQTT] Failed to save usage log to database: {str(log_err)}")

            base_url = getattr(config, 'ORKOFLEET_BASE_URL')
            api_url = f"{base_url}/api/v2/charge-sessions/add-usage-data"
            headers = {"Content-Type": "application/json"}
            
            # Always log outgoing to terminal
            logger.info(f"[MQTT] -> Usage API Payload: {json.dumps(payload)}")
            
            response = requests.post(api_url, json=payload, headers=headers, timeout=5)
            logger.info(f"[MQTT] Forwarded {device_id} usage to API. Status: {response.status_code}")

            # Only save timestamp after successful API post
            if new_timestamp:
                self.last_usage_timestamps[device_id] = new_timestamp

            # Update last usage state in memory for stale-completion watchdog
            self.last_incomplete_usage[device_id] = {
                "payload": dict(payload),
                "received_at": datetime.now().timestamp()
            }
            
            # Restore terminal logging of response (but not database)
            try:
                resp_data = response.json()
                logger.info(f"[MQTT] Usage API Response: {json.dumps(resp_data)}")
            except:
                logger.info(f"[MQTT] Usage API Response: {response.text}")

        except Exception as e:
            logger.error(f"[MQTT] Error handling device usage for {device_id}: {str(e)}")

    def check_stale_usage_completions(self):
        """
        Called by the scheduler every 30 seconds.
        Checks in-memory last usage data, finds any device whose last usage had
        is_completed=0 for more than 3 minutes, and auto-sends a completion payload.
        """
        try:
            now = datetime.now().timestamp()
            stale_threshold = 3 * 60  # 3 minutes in seconds

            for device_id, entry in list(self.last_incomplete_usage.items()):
                if entry["payload"].get("is_completed") != 0:
                    continue
                elapsed = now - entry["received_at"]
                if elapsed >= stale_threshold:
                    completion_payload = dict(entry["payload"])
                    completion_payload["is_completed"] = 1

                    # Save completion to UsageLogging before sending to API
                    try:
                        from esp32OTA.UsageLogging.controllers.UsageLoggingController import UsageLoggingController
                        from esp32OTA import app
                        
                        usage_log_data = {
                            constants.USAGE_LOGGING__DEVICE_ID: str(device_id),
                            constants.USAGE_LOGGING__TIMESTAMP: str(common_utils.get_time_iso()),
                            constants.USAGE_LOGGING__SOCKET_ID: completion_payload["socket_id"],
                            constants.USAGE_LOGGING__SESSION_ID: str(completion_payload["session_id"]),
                            constants.USAGE_LOGGING__CONSUMPTION: completion_payload["consumption"],
                            constants.USAGE_LOGGING__CURRENT: completion_payload["current"],
                            constants.USAGE_LOGGING__VOLTAGE: completion_payload["voltage"],
                            constants.USAGE_LOGGING__DURATION: completion_payload["duration"],
                            constants.USAGE_LOGGING__IS_COMPLETED: completion_payload["is_completed"]
                        }
                        
                        with app.app_context():
                            UsageLoggingController.log_usage(data=usage_log_data)
                            logger.info(f"[MQTT] Stale usage completion saved to database for {device_id}")
                    except Exception as log_err:
                        logger.error(f"[MQTT] Failed to save stale usage log to database: {str(log_err)}")

                    base_url = getattr(config, 'ORKOFLEET_BASE_URL')
                    api_url = f"{base_url}/api/v2/charge-sessions/add-usage-data"
                    headers = {"Content-Type": "application/json"}

                    logger.info(f"[MQTT] Auto-completing stale usage for {device_id} (elapsed: {elapsed:.0f}s): {json.dumps(completion_payload)}")

                    mqtt_log = {
                        "event": "auto_completion",
                        "request": {
                            "url": api_url,
                            "payload": completion_payload
                        }
                    }

                    try:
                        response = requests.post(api_url, json=completion_payload, headers=headers, timeout=5)
                        logger.info(f"[MQTT] Auto-completion response for {device_id}: {response.status_code}")
                        try:
                            resp_body = response.json()
                        except Exception:
                            resp_body = response.text
                        mqtt_log["response"] = {
                            "status_code": response.status_code,
                            "body": resp_body
                        }
                    except Exception as post_err:
                        logger.error(f"[MQTT] Auto-completion POST failed for {device_id}: {str(post_err)}")
                        mqtt_log["response"] = {"error": str(post_err)}

                    self.publish(f"ZV/DEVICES/{device_id}/auto_completion", mqtt_log)
                    del self.last_incomplete_usage[device_id]

        except Exception as e:
            logger.error(f"[MQTT] Error in stale usage check: {str(e)}")

    def handle_config_request(self, device_id):
        """
        Handles config request from device (send_config = 1).
        Fetches device config and publishes shortened variables and QR code to configupdate topic.
        """
        try:
            logger.info(f"[MQTT] handle_config_request called for device: {device_id}")
            
            # Fetch device from database
            device = Device.objects(device_id=str(device_id)).first()
            logger.info(f"[MQTT] Database query attempt 1 result: {device is not None}")
            
            if not device:
                # Fallback - try iterating through devices
                logger.info(f"[MQTT] Attempting fallback device lookup for {device_id}")
                for d in Device.objects.only('device_id', 'variables', 'qr_code'):
                    if str(d.device_id) == str(device_id):
                        device = d
                        logger.info(f"[MQTT] Device found via fallback lookup")
                        break
            
            if not device:
                logger.warning(f"[MQTT] Device {device_id} not found in database for config request")
                return
            
            logger.info(f"[MQTT] Device found: {device_id}, has variables: {device.variables is not None}")
            
            # Build config update payload
            topic = f"ZV/DEVICES/{device.device_id}/configupdate"
            payload = {
                "t": int(datetime.now().timestamp()),
                "variables": dict(device.variables),
                "qr_code": device.qr_code
            }
            
            logger.info(f"[MQTT] Publishing config to {topic}")
            # Publish to MQTT
            self.publish(topic, payload)
            logger.info(f"[MQTT] Config sent to {device_id}")
            
        except Exception as e:
            logger.error(f"[MQTT] Error handling config request for {device_id}: {str(e)}", exc_info=True)

    def handle_setconfig(self, device_id, data):
        """
        Handles setconfig payload from a device.
        Updates hw_version and fully replaces variables on the matching device.
        Expected payload: {"hw_version": "0.4", "variables": {...}}
        """
        try:
            # Primary lookup
            device = Device.objects(device_id=str(device_id)).first()

            # Fallback: SequenceField stores raw int in MongoDB; decorated "DV-X" only
            # matches on the Python side, so iterate and compare like the controller does
            if not device:
                for d in Device.objects.all():
                    if str(d.device_id) == str(device_id):
                        device = d
                        break

            if not device:
                logger.warning(f"[MQTT] Device {device_id} not found for setconfig")
                return

            # Build update using MongoDB ObjectId (same as db_update_single_record in DeviceController)
            update_kwargs = {}
            if "hw_version" in data:
                update_kwargs["set__hw_version"] = data["hw_version"]
            if "variables" in data:
                update_kwargs["set__variables"] = data["variables"]

            if not update_kwargs:
                logger.warning(f"[MQTT] setconfig for {device_id}: no hw_version or variables in payload")
                return

            Device.objects(id=device.id).update_one(**update_kwargs)
            logger.info(f"[MQTT] setconfig applied for {device_id}: {update_kwargs}")
        except Exception as e:
            logger.error(f"[MQTT] Error handling setconfig for {device_id}: {str(e)}", exc_info=True)

    def on_disconnect(self, client, userdata, disconnect_flags, reason_code, properties=None):
        self.connected = False
        logger.warning(f"[MQTT] Disconnected: {reason_code}")
        # Attempt to reconnect after 5 seconds
        logger.info("[MQTT] Attempting to reconnect in 5 seconds...")
        threading.Timer(5.0, self.reconnect).start()

    def reconnect(self):
        """Attempt to reconnect to MQTT broker"""
        try:
            if not self.connected:
                logger.info("[MQTT] Reconnecting to broker...")
                self.client.reconnect()
        except Exception as e:
            logger.error(f"[MQTT] Reconnection failed: {str(e)}")
            # Try again in 5 seconds
            threading.Timer(5.0, self.reconnect).start()

    def start(self):
        try:
            # Set keep-alive to 60 seconds to detect disconnections faster
            self.client.connect(self.broker_host, self.broker_port, keepalive=60)
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
