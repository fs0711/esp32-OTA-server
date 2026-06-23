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
            client.subscribe("$SYS/broker/#", qos=0)
            client.subscribe("ZV/DEVICES/+/status/#", qos=1)
            client.subscribe("ZV/DEVICES/+/usage/#", qos=1)
            client.subscribe("ZV/DEVICES/+/ping", qos=1)
            client.subscribe("ZV/DEVICES/+/command", qos=1)
            client.subscribe("ZV/DEVICES/+/send_config", qos=1)
            client.subscribe("ZV/DEVICES/+/configuration", qos=1)
            client.subscribe("ZV/DEVICES/+/setconfig", qos=1)
            client.subscribe("ZV/DEVICES/+/getfirmware", qos=1)
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
                elif len(topic_parts) >= 3 and "ping" in topic:
                    device_id = topic_parts[2]
                    try:
                        data = json.loads(payload_str)
                        logger.info(f"[MQTT] Ping received from {device_id}: {payload_str}")
                        self.handle_ping(device_id, data)
                    except json.JSONDecodeError:
                        logger.error(f"[MQTT] Failed to decode ping payload for {device_id}")
                
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
                if len(topic_parts) >= 4 and topic_parts[3] == "configuration":
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

                # Handle getfirmware topic
                if len(topic_parts) >= 4 and topic_parts[3] == "getfirmware":
                    device_id = topic_parts[2]
                    logger.info(f"[MQTT] getfirmware topic request received from {device_id}")
                    self.handle_firmware_request(device_id, payload_str)
        except Exception as e:
            logger.error(f"[MQTT] Error in on_message: {str(e)}")

    def handle_ping(self, device_id, data):
        """
        Handles ping from device.
        Updates last_updated and status online in connection of device.
        """
        try:
            # Primary lookup
            device = Device.objects(device_id=str(device_id)).first()

            if not device:
                for d in Device.objects.only('device_id', 'connection'):
                    if str(d.device_id) == str(device_id):
                        device = d
                        break

            if not device:
                return

            timestamp = data.get("t")
            if timestamp:
                last_updated = common_utils.epoch_to_datetime(timestamp * 1000)
                Device.objects(id=device.id).update_one(
                    **{f"set__{constants.DEVICE__CONNECTION}": {"last_updated": last_updated, "status": "online"}}
                )
                logger.info(f"[MQTT] Ping status updated for {device_id}: online at {last_updated}")
        except Exception as e:
            logger.error(f"[MQTT] Error handling ping for {device_id}: {str(e)}", exc_info=True)

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

            client_id = getattr(device, 'client_id', None)
            if not client_id:
                connection_data = getattr(device, 'connection', {})
                if isinstance(connection_data, dict):
                    client_id = connection_data.get('client_id')

            if not client_id:
                return


            # 2. Map incoming status format to requested API format
            # Device sends: {"t": 123, "s": [{"id": 2, "st": 0, "sg": "w", "e": "E2"}], "e": []}
            incoming_s = raw_data.get("s", [])
            mapped_s = []
            
            for item in incoming_s:
                # Signal type mapping: w -> wifi, g -> gsm, empty defaults to wifi
                signal_raw = item.get("sg")
                if signal_raw == "w" or not signal_raw:
                    signal_mapped = "wifi"
                elif signal_raw == "g":
                    signal_mapped = "gsm"
                else:
                    signal_mapped = signal_raw

                # Handle error field 'e': could be string "E2", list ["E2"], or 0/null
                e_raw = item.get("e")
                if isinstance(e_raw, list):
                    e_mapped = [str(x) for x in e_raw]
                elif e_raw is not None:
                    e_mapped = [str(e_raw)]
                else:
                    e_mapped = []

                mapped_s.append({
                    "id": item.get("id"),
                    "status": item.get("st"), # st -> status
                    "signal_type": signal_mapped,
                    "e": e_mapped
                })
            
            # Root error field: normalize to list, default to empty
            root_errors_raw = raw_data.get("e")
            if isinstance(root_errors_raw, list):
                root_errors = [str(x) for x in root_errors_raw]
            elif root_errors_raw is not None:
                root_errors = [str(root_errors_raw)]
            else:
                root_errors = []
            
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

            # Save to database log
            from esp32OTA.GatewayLogging.controllers.GatewayLoggingController import GatewayLoggingController
            from esp32OTA import app
            with app.app_context():
                GatewayLoggingController.log_gateway_activity(json.dumps(payload), "sent", device_id)

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
                "duration": (usage_inner.get("d") or 0) * 1000, # Multiply duration by 1000
                "is_completed": usage_inner.get("is")
            }

            # Save to UsageLogging first then send to API and update
            log_id = None
            try:
                from esp32OTA.UsageLogging.controllers.UsageLoggingController import UsageLoggingController
                from esp32OTA import app
                
                usage_log_data = {
                    constants.USAGE_LOGGING__DEVICE_ID: str(device_id),
                    constants.USAGE_LOGGING__TIMESTAMP: str(new_timestamp if new_timestamp is not None else common_utils.get_time_iso()),
                    constants.USAGE_LOGGING__SOCKET_ID: payload["socket_id"],
                    constants.USAGE_LOGGING__SESSION_ID: str(payload["session_id"]),
                    constants.USAGE_LOGGING__CONSUMPTION: payload["consumption"],
                    constants.USAGE_LOGGING__CURRENT: payload["current"],
                    constants.USAGE_LOGGING__VOLTAGE: payload["voltage"],
                    constants.USAGE_LOGGING__DURATION: payload["duration"],
                    constants.USAGE_LOGGING__IS_COMPLETED: payload["is_completed"],
                    constants.USAGE_LOGGING__AUTO_COMPLETION: False
                }
                
                with app.app_context():
                    usage_obj = UsageLoggingController.log_usage(data=usage_log_data)
                    if usage_obj:
                        log_id = str(usage_obj.id)
                        logger.info(f"[MQTT] Usage data pre-saved to database for {device_id}, ID: {log_id}")
            except Exception as log_err:
                logger.error(f"[MQTT] Failed to pre-save usage log to database: {str(log_err)}")

            base_url = getattr(config, 'ORKOFLEET_BASE_URL')
            api_url = f"{base_url}/api/v2/charge-sessions/add-usage-data"
            headers = {"Content-Type": "application/json"}
            
            # Always log outgoing to terminal
            logger.info(f"[MQTT] -> Usage API Payload: {json.dumps(payload)}")
            
            api_response_data = {}
            api_response_code = None
            try:
                response = requests.post(api_url, json=payload, headers=headers, timeout=5)
                logger.info(f"[MQTT] Forwarded {device_id} usage to API. Status: {response.status_code}")
                api_response_code = response.status_code
                
                try:
                    api_response_data = response.json()
                    logger.info(f"[MQTT] Usage API Response: {json.dumps(api_response_data)}")
                except:
                    api_response_data = {"raw_response": response.text}
                    logger.info(f"[MQTT] Usage API Response: {response.text}")
                
                # Only save timestamp after successful API post
                if response.status_code in [200, 201] and new_timestamp:
                    self.last_usage_timestamps[device_id] = new_timestamp
            except Exception as api_err:
                logger.error(f"[MQTT] API Post failed for {device_id}: {str(api_err)}")
                api_response_data = {"error": str(api_err)}

            # Update existing log with API result
            if log_id:
                try:
                    update_data = {
                        f"set__{constants.USAGE_LOGGING__RESPONSE_CODE}": api_response_code,
                        f"set__{constants.USAGE_LOGGING__API_RESPONSE}": api_response_data
                    }
                    with app.app_context():
                        UsageLoggingController.update_usage(log_id=log_id, data=update_data)
                        logger.info(f"[MQTT] Updated usage log {log_id} with API response")
                except Exception as up_err:
                    logger.error(f"[MQTT] Failed to update usage log {log_id}: {str(up_err)}")

            # Update last usage state in memory for stale-completion watchdog
            self.last_incomplete_usage[device_id] = {
                "payload": dict(payload),
                "received_at": datetime.now().timestamp(),
                "device_timestamp": new_timestamp
            }

        except Exception as e:
            logger.error(f"[MQTT] Error handling device usage for {device_id}: {str(e)}")

    def check_stale_usage_completions(self):
        """
        Called by the scheduler every 30 seconds.
        Checks in-memory last usage data, finds any device whose last usage had
        is_completed=0 for more than 10 minutes, and auto-sends a completion payload.
        """
        try:
            now = datetime.now().timestamp()
            stale_threshold = 10 * 60  # 10 minutes in seconds

            for device_id, entry in list(self.last_incomplete_usage.items()):
                if entry["payload"].get("is_completed") != 0:
                    continue
                elapsed = now - entry["received_at"]
                if elapsed >= stale_threshold:
                    completion_payload = dict(entry["payload"])
                    completion_payload["is_completed"] = 1

                    # Save completion to UsageLogging then send to API and update
                    log_id = None
                    try:
                        from esp32OTA.UsageLogging.controllers.UsageLoggingController import UsageLoggingController
                        from esp32OTA import app
                        
                        usage_log_data = {
                            constants.USAGE_LOGGING__DEVICE_ID: str(device_id),
                            constants.USAGE_LOGGING__TIMESTAMP: str(entry.get("device_timestamp") if entry.get("device_timestamp") is not None else common_utils.get_time_iso()),
                            constants.USAGE_LOGGING__SOCKET_ID: completion_payload["socket_id"],
                            constants.USAGE_LOGGING__SESSION_ID: str(completion_payload["session_id"]),
                            constants.USAGE_LOGGING__CONSUMPTION: completion_payload["consumption"],
                            constants.USAGE_LOGGING__CURRENT: completion_payload["current"],
                            constants.USAGE_LOGGING__VOLTAGE: completion_payload["voltage"],
                            constants.USAGE_LOGGING__DURATION: completion_payload["duration"],
                            constants.USAGE_LOGGING__IS_COMPLETED: completion_payload["is_completed"],
                            constants.USAGE_LOGGING__AUTO_COMPLETION: True
                        }
                        
                        with app.app_context():
                            usage_obj = UsageLoggingController.log_usage(data=usage_log_data)
                            if usage_obj:
                                log_id = str(usage_obj.id)
                                logger.info(f"[MQTT] Stale usage pre-saved to database for {device_id}, ID: {log_id}")
                    except Exception as log_err:
                        logger.error(f"[MQTT] Failed to pre-save stale usage log to database: {str(log_err)}")

                    base_url = getattr(config, 'ORKOFLEET_BASE_URL')
                    api_url = f"{base_url}/api/v2/charge-sessions/add-usage-data"
                    headers = {"Content-Type": "application/json"}

                    logger.info(f"[MQTT] Auto-completing stale usage for {device_id} (elapsed: {elapsed:.0f}s): {json.dumps(completion_payload)}")

                    api_response_data = {}
                    api_response_code = None
                    try:
                        response = requests.post(api_url, json=completion_payload, headers=headers, timeout=5)
                        logger.info(f"[MQTT] Auto-completion response for {device_id}: {response.status_code}")
                        api_response_code = response.status_code
                        try:
                            api_response_data = response.json()
                        except Exception:
                            api_response_data = {"raw_response": response.text}
                    except Exception as post_err:
                        logger.error(f"[MQTT] Auto-completion POST failed for {device_id}: {str(post_err)}")
                        api_response_data = {"error": str(post_err)}

                    # Update record with API result
                    if log_id:
                        try:
                            update_data = {
                                f"set__{constants.USAGE_LOGGING__RESPONSE_CODE}": api_response_code,
                                f"set__{constants.USAGE_LOGGING__API_RESPONSE}": api_response_data
                            }
                            with app.app_context():
                                UsageLoggingController.update_usage(log_id=log_id, data=update_data)
                                logger.info(f"[MQTT] Updated stale usage log {log_id} with API response")
                        except Exception as up_err:
                            logger.error(f"[MQTT] Failed to update stale usage log {log_id}: {str(up_err)}")
                        except Exception as log_err:
                            logger.error(f"[MQTT] Failed to save stale usage log to database: {str(log_err)}")

                    mqtt_log = {
                        "event": "auto_completion",
                        "request": {
                            "url": api_url,
                            "payload": completion_payload
                        },
                        "response": api_response_data
                    }

                    self.publish(f"ZV/DEVICES/{device_id}/auto_completion", mqtt_log)

                    # After auto-completion, send socket status update to Orko
                    try:
                        device = Device.objects(device_id=str(device_id)).first()
                        if not device:
                            for d in Device.objects.only('device_id', 'client_id'):
                                if str(d.device_id) == str(device_id):
                                    device = d
                                    break

                        client_id = getattr(device, 'client_id', None) if device else None
                        if client_id:
                            status_payload = {
                                "c_s_id": int(client_id) if str(client_id).isdigit() else client_id,
                                "s": [
                                    {
                                        "id": 1,
                                        "status": 0,
                                        "signal_type": "wifi",
                                        "e": ["E0"]
                                    }
                                ],
                                "e": []
                            }
                            status_url = f"{base_url}/api/v2/power-sockets/status"
                            logger.info(f"[MQTT] Sending post-autocomplete status for {device_id}: {json.dumps(status_payload)}")
                            status_response = requests.post(status_url, json=status_payload, headers=headers, timeout=5)
                            logger.info(f"[MQTT] Post-autocomplete status response for {device_id}: {status_response.status_code}")
                            try:
                                status_response_data = status_response.json()
                            except Exception:
                                status_response_data = {"raw_response": status_response.text}

                            mqtt_status_log = {
                                "event": "post_autocomplete_status",
                                "request": {
                                    "url": status_url,
                                    "payload": status_payload
                                },
                                "response": status_response_data
                            }
                            self.publish(f"ZV/DEVICES/{device_id}/auto_completion_status", mqtt_status_log)
                        else:
                            logger.warning(f"[MQTT] Could not find client_id for {device_id}, skipping post-autocomplete status")
                    except Exception as status_err:
                        logger.error(f"[MQTT] Failed to send post-autocomplete status for {device_id}: {str(status_err)}")

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

    def handle_firmware_request(self, device_id, value):
        """
        Handles firmware request from device (getfirmware = 1).
        Queries device and its assigned firmware, then publishes details back to MQTT.
        """
        try:
            try:
                data = json.loads(value)
                if not isinstance(data, dict):
                    data = {"getfirmware": data}
            except (json.JSONDecodeError, TypeError):
                data = {}
            if data.get("getfirmware") != 1:
                return
                
            # Primary lookup
            device = Device.objects(device_id=str(device_id)).first()

            if not device:
                for d in Device.objects.all():
                    if str(d.device_id) == str(device_id):
                        device = d
                        break

            if device and device.fw_file:
                firmware = device.fw_file.fetch()
                if firmware:
                    mqtt_payload = {
                        "t": common_utils.get_time_iso(),
                        "f_f": str(firmware.id),
                        "f_v": str(device.fw_version) if device.fw_version else "",
                        "h_v": str(device.hw_version) if device.hw_version else "",
                        "n_v": str(firmware.version) if firmware.version else "",
                        "u_p": str(firmware.update_path) if firmware.update_path else ""
                    }
                    
                    # Publish to MQTT firmware topic
                    self.publish_firmware_update(device_id, mqtt_payload)
                    logger.info(f"[MQTT] Published firmware update details for {device_id}")
                else:
                    logger.warning(f"[MQTT] Firmware record not found for device {device_id}")
            else:
                logger.warning(f"[MQTT] Device {device_id} not found or has no assigned firmware")

        except Exception as e:
            logger.error(f"[MQTT] Error handling firmware request for {device_id}: {str(e)}", exc_info=True)

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
            self.client.publish(topic, payload, qos=1, retain=True)
            logger.info(f"[MQTT] Published firmware update to {topic}: {payload}")
        except Exception as e:
            logger.error(f"[MQTT] Failed to publish firmware update to {topic}: {str(e)}")

    def publish(self, topic, message, qos=1, retain=True):
        """
        Publishes a message to a specific topic.
        """
        try:
            if isinstance(message, (dict, list)):
                payload = json.dumps(message)
            else:
                payload = str(message)

            self.client.publish(topic, payload, qos=qos, retain=retain)
            logger.info(f"[MQTT] Published to {topic}: {payload}")
            return True
        except Exception as e:
            logger.error(f"[MQTT] Failed to publish to {topic}: {str(e)}")
            return False

mqtt_service = MQTTClientService()
