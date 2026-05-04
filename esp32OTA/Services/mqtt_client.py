import paho.mqtt.client as mqtt
import logging
import json
import threading
import requests
from datetime import datetime
from esp32OTA.config import config
from esp32OTA.DeviceManagement.models.Device import Device

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
        
        self.broker_host = "127.0.0.1" 
        self.broker_port = 1884 # Testing port as per mosquitto.conf
        
        self.broker_stats = {}
        self.device_data = {}
        self.last_timestamps = {}  # Track last timestamp per device
        self.last_usage_timestamps = {} # Track last usage timestamp per device
        self._initialized = True

    def on_connect(self, client, userdata, flags, reason_code, properties=None):
        if reason_code == 0:
            logger.info("[MQTT] Connected successfully")
            # Subscribe to stats and device topics
            client.subscribe("$SYS/broker/#")
            client.subscribe("devices/+/status/#")
            client.subscribe("devices/+/usage/#")
        else:
            logger.error(f"[MQTT] Connection failed with code {reason_code}")

    def on_message(self, client, userdata, message):
        try:
            topic = message.topic
            payload_str = message.payload.decode()
            
            if topic.startswith("$SYS/broker/"):
                stat_key = topic.replace("$SYS/broker/", "")
                self.broker_stats[stat_key] = payload_str
            elif topic.startswith("devices/"):
                # Handle incoming status from devices
                # Expected topic format: devices/DV-2/status
                topic_parts = topic.split('/')
                if len(topic_parts) >= 2 and "status" in topic:
                    device_id = topic_parts[1]
                    try:
                        data = json.loads(payload_str)
                        # Identify if this is a new message by timestamp BEFORE logging
                        new_timestamp = data.get("timestamp")
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
                elif len(topic_parts) >= 2 and "usage" in topic:
                    device_id = topic_parts[1]
                    try:
                        data = json.loads(payload_str)
                        new_timestamp = data.get("timestamp")
                        if new_timestamp is not None:
                            if self.last_usage_timestamps.get(device_id) == new_timestamp:
                                return
                        
                        logger.info(f"[MQTT] Unique usage for {device_id}: {payload_str}")
                        self.handle_device_usage(device_id, data)
                    except json.JSONDecodeError:
                        logger.error(f"[MQTT] Failed to decode usage payload for {device_id}")
        except Exception as e:
            logger.error(f"[MQTT] Error in on_message: {str(e)}")

    def handle_device_status(self, device_id, raw_data):
        """
        Processes incoming device status, finds client_id (c_s_id),
        checks for duplicate timestamps, and forwards to the external status API.
        """
        try:
            # 0. Deduplicate by timestamp
            new_timestamp = raw_data.get("timestamp")
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
                client_id = getattr(device, 'client_id', None)
                if not client_id:
                    connection_data = getattr(device, 'connection', {})
                    if isinstance(connection_data, dict):
                        client_id = connection_data.get('client_id')
            
            if not client_id:
                return

            # Update GatewayService with local knowledge for heartbeats
            from esp32OTA.Services.GatewayService import GatewayService
            from esp32OTA import app
            with app.app_context():
                GatewayService._last_data[device_id] = {
                    "c_s_id": client_id,
                    "online": True,
                    "last_seen": datetime.now().isoformat()
                }

            # 2. Map incoming status format to requested API format
            # Device sends: {"timestamp": 123, "s": [{"id": 2, "st": 0, "sg": "w", "e": ["E2"]}]}
            incoming_s = raw_data.get("s", [])
            mapped_s = []
            
            for item in incoming_s:
                mapped_s.append({
                    "id": item.get("id"),
                    "status": item.get("st"), # st -> status
                    "signal_type": "wifi" if item.get("sg") == "w" else item.get("sg"), # sg -> signal_type
                    "e": item.get("e", [])
                })

            payload = {
                "c_s_id": int(client_id) if str(client_id).isdigit() else client_id,
                "s": mapped_s,
                "e": []
            }

            # 3. Post to API
            api_url = "https://smartswitch.orkofleet.com/api/v2/power-sockets/status"
            headers = {
                "Content-Type": "application/json"
            }
            logger.info(f"[MQTT] -> API Payload: {json.dumps(payload)}")
            
            # Save outgoing log
            from esp32OTA.GatewayLogging.controllers.GatewayLoggingController import GatewayLoggingController
            from esp32OTA import app
            with app.app_context():
                GatewayLoggingController.log_gateway_activity(json.dumps(payload), "sent")

            response = requests.post(api_url, json=payload, headers=headers, timeout=5)
            logger.info(f"[MQTT] Forwarded {device_id} status to API. Status: {response.status_code}")
            
            try:
                resp_data = response.json()
                logger.info(f"[MQTT] API Response: {json.dumps(resp_data)}")
                # Save incoming log
                with app.app_context():
                    GatewayLoggingController.log_gateway_activity(json.dumps(resp_data), "received")
            except:
                logger.info(f"[MQTT] API Response: {response.text}")
                # Save incoming log (raw text)
                with app.app_context():
                    GatewayLoggingController.log_gateway_activity(response.text, "received")
            
        except Exception as e:
            logger.error(f"[MQTT] Error handling device status for {device_id}: {str(e)}")

    def handle_device_usage(self, device_id, raw_data):
        """
        Processes incoming device usage, maps fields, and posts to the usage API.
        """
        try:
            new_timestamp = raw_data.get("timestamp")
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

            api_url = "https://smartswitch.orkofleet.com/api/v2/charge-sessions/add-usage-data"
            headers = {"Content-Type": "application/json"}
            
            logger.info(f"[MQTT] -> Usage API Payload: {json.dumps(payload)}")
            
            # Save outgoing log
            from esp32OTA.GatewayLogging.controllers.GatewayLoggingController import GatewayLoggingController
            from esp32OTA import app
            with app.app_context():
                GatewayLoggingController.log_gateway_activity(json.dumps(payload), "sent")

            response = requests.post(api_url, json=payload, headers=headers, timeout=5)
            logger.info(f"[MQTT] Forwarded {device_id} usage to API. Status: {response.status_code}")
            
            try:
                resp_data = response.json()
                logger.info(f"[MQTT] Usage API Response: {json.dumps(resp_data)}")
                # Save incoming log
                with app.app_context():
                    GatewayLoggingController.log_gateway_activity(json.dumps(resp_data), "received")
            except:
                logger.info(f"[MQTT] Usage API Response: {response.text}")
                # Save incoming log (raw text)
                with app.app_context():
                    GatewayLoggingController.log_gateway_activity(response.text, "received")

        except Exception as e:
            logger.error(f"[MQTT] Error handling device usage for {device_id}: {str(e)}")

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

mqtt_service = MQTTClientService()
