# Python imports
import logging

# Framework imports
from flask import jsonify, render_template, request
from datetime import datetime

# Setup logger
logger = logging.getLogger(__name__)


# Local imports
from esp32OTA import app, config
from esp32OTA.Services.GatewayService import GatewayService
from esp32OTA.Services.ConfigController import ConfigController
from esp32OTA.generic.services.utils import constants, decorators, response_utils, common_utils
from esp32OTA.UserManagement.views.users import users_bp
from esp32OTA.DeviceManagement.views.device import device_bp
from esp32OTA.DeviceManagement.views.device_type import device_type_bp
from esp32OTA.DeviceManagement.views.mqtt_auth import mqtt_auth_bp
from esp32OTA.FirmwareManagement.views.firmware import firmware_bp
from esp32OTA.GatewayLogging.views.gateway_logging import gateway_logging_bp
from esp32OTA.APITokenManagement.views.apitokens import api_token_bp
from esp32OTA.UsageLogging.views.usage_logging import usage_logging_bp
from esp32OTA.PingLogging.views.ping_logging import ping_logging_bp


@app.route("/api/redis/status", methods=["GET"])
def redis_status():
    """Check Redis connection and return basic stats."""
    from esp32OTA.Services.redis_client import redis_client
    r = redis_client._r
    if not r:
        return jsonify({"connected": False, "error": "Redis client not initialised"}), 503
    try:
        r.ping()
        info = r.info("server")
        topics = redis_client.get_all_topics()
        return jsonify({
            "connected": True,
            "host": r.connection_pool.connection_kwargs.get("host"),
            "port": r.connection_pool.connection_kwargs.get("port"),
            "redis_version": info.get("redis_version"),
            "uptime_seconds": info.get("uptime_in_seconds"),
            "topic_count": len(topics),
            "topics": topics
        })
    except Exception as exc:
        return jsonify({"connected": False, "error": str(exc)}), 503


@app.route("/api/static-data", methods=["GET"])
def static_data_view():
    return jsonify(constants.STATIC_DATA)


@app.route("/", methods=["GET"])
def login_page():
    return render_template("login.html")


@app.route("/gateway", methods=["GET"])
def gateway_dashboard():
    return render_template("index.html")


@app.route("/api/gateway/data", methods=["GET"])
def gateway_data():
    from esp32OTA.DeviceManagement.models.Device import Device
    from datetime import datetime, timedelta, timezone
    
    is_connected = GatewayService.get_mqtt_status()
    broker_stats = GatewayService.get_broker_stats()
    
    # Fetch devices directly from Device table instead of in-memory cache
    try:
        current_time = datetime.now(timezone.utc)
        heartbeat_threshold = timedelta(minutes=2)
        
        # Get all active devices with client_id
        db_devices = Device.objects(
            client_id__ne=None, 
            status=constants.OBJECT_STATUS_ACTIVE
        ).only('device_id', 'connection', 'created_on')
        
        devices = []
        for device in db_devices:
            connection = device.connection or {}
            last_update = connection.get('last_updated', '')
            device_status = connection.get('status', 'offline')
            
            # Use created_on as fallback if last_update is empty
            if not last_update and device.created_on:
                last_update = device.created_on.isoformat() if hasattr(device.created_on, 'isoformat') else str(device.created_on)
            
            # Determine if device is online based on device status field
            is_online = device_status.lower() == 'online'
            
            devices.append({
                "id": str(device.device_id),
                "online": is_online,
                "last_seen": last_update
            })
        
        # Sort devices by ID for consistent display
        devices = sorted(devices, key=lambda x: x['id'])
        
    except Exception as e:
        logger.error(f"Error fetching devices from database: {str(e)}")
        devices = []
    
    return jsonify({
        "mqtt_connected": is_connected,
        "broker_stats": broker_stats,
        "devices": devices
    })


@app.route("/api/gateway/logs", methods=["GET"])
def gateway_logs():
    logs = GatewayService.get_live_logs()
    return jsonify({"logs": logs})


@app.route("/api/gateway/config", methods=["GET", "POST"])
def gateway_config():
    if request.method == "GET":
        return ConfigController.get_config()
    
    data = common_utils.posted()
    return ConfigController.update_config(data)


@app.route("/api-docs", methods=["GET"])
def api_docs():
    api_list = []
    
    for rule in app.url_map.iter_rules():
        if rule.endpoint == 'static' or 'api_docs' in rule.endpoint:
            continue
            
        view_func = app.view_functions[rule.endpoint]
        methods = list(rule.methods - {'HEAD', 'OPTIONS'})
        
        # Determine the name based on whether it's a blueprint or main app
        name = rule.endpoint.split('.')[-1] if '.' in rule.endpoint else rule.endpoint
        
        api_info = {
            "endpoint": rule.rule,
            "methods": methods,
            "name": name,
            "full_endpoint": rule.endpoint,
            "doc": view_func.__doc__ if view_func.__doc__ else "No description available.",
            "module": view_func.__module__,
            "required_fields": [],
            "optional_fields": [],
            "is_authenticated": False,
            "required_headers": ["Content-Type"],
            "auth_headers": ["x-session-key", "x-session-type"],
            "roles_allowed": []
        }
        
        # Try to detect decorators and extract information
        try:
            if hasattr(view_func, '__closure__') and view_func.__closure__:
                for cell in view_func.__closure__:
                    contents = cell.cell_contents
                    
                    # Check for required/optional fields
                    if isinstance(contents, list):
                        if not api_info["required_fields"]:
                            api_info["required_fields"] = contents
                        elif not api_info["optional_fields"]:
                            api_info["optional_fields"] = contents
                    
                    # Check for authentication decorator
                    if isinstance(contents, bool) or (isinstance(contents, str) and 'authenticated' in str(contents)):
                        api_info["is_authenticated"] = True
                        if "Authorization" not in api_info["required_headers"]:
                            api_info["required_headers"].append("Authorization")
                    
                    # Also look for nested closure (the actual decorator)
                    if callable(contents) and hasattr(contents, '__closure__') and contents.__closure__:
                        for inner_cell in contents.__closure__:
                            inner_contents = inner_cell.cell_contents
                            if isinstance(inner_contents, list):
                                if not api_info["required_fields"]:
                                    api_info["required_fields"] = inner_contents
                                elif not api_info["optional_fields"]:
                                    api_info["optional_fields"] = inner_contents
                                # Check if it's roles info
                                elif all(isinstance(x, int) for x in inner_contents if isinstance(x, int)):
                                    api_info["roles_allowed"] = inner_contents
        except:
            pass
        
        # Check endpoint name/path for common patterns
        if '/login' in rule.rule and rule.methods != {'HEAD', 'OPTIONS', 'GET'}:
            if "Authorization" not in api_info["required_headers"]:
                pass  # Login doesn't need auth
        elif any(pattern in rule.rule for pattern in ['/create', '/update', '/delete', '/force', '/read']):
            api_info["is_authenticated"] = True
            if "Authorization" not in api_info["required_headers"]:
                api_info["required_headers"].append("Authorization")

        api_list.append(api_info)
        
    return render_template("api_docs.html", apis=api_list)


@app.route("/logs", methods=["GET"])
def logs_page():
    """Display application logs page"""
    return render_template("logs.html")


@app.route("/app-logs", methods=["GET"])
def app_logs_page():
    """Display app.log viewer page"""
    return render_template("app_logs.html")


@app.route("/api/app-logs", methods=["GET"])
def app_logs_api():
    """
    Efficiently tail and paginate /var/log/esp32ota/app.log (or access/error logs).
    Reads only the last MAX_TAIL lines so large files never block the server.
    Query params: file, page, per_page, level, search
    """
    import os
    import re
    from collections import deque

    LOG_FILES = {
        "app":    os.path.join(config.log_directory_path, "app.log"),
        "access": os.path.join(config.log_directory_path, "access.log"),
        "error":  os.path.join(config.log_directory_path, "error.log"),
    }
    MAX_TAIL   = 5000   # lines kept in memory at most
    PER_PAGE   = min(int(request.args.get("per_page", 200)), 500)
    page       = max(int(request.args.get("page", 1)), 1)
    file_key   = request.args.get("file", "app")
    level_filt = request.args.get("level", "").upper().strip()
    search     = request.args.get("search", "").strip().lower()
    date_from  = request.args.get("date_from", "").strip()   # YYYY-MM-DD
    date_to    = request.args.get("date_to",   "").strip()   # YYYY-MM-DD

    filepath = LOG_FILES.get(file_key, LOG_FILES["app"])

    # ── file existence check ──────────────────────────────────────────────────
    if not os.path.exists(filepath):
        return jsonify({"lines": [], "total": 0, "page": 1, "pages": 1,
                        "file_size": 0, "file": file_key,
                        "error": f"Log file not found: {filepath}"})

    file_size = os.path.getsize(filepath)

    # ── efficient tail: read chunks from EOF until we have MAX_TAIL lines ─────
    def tail_file(path, max_lines):
        buf = deque()
        chunk = 65536  # 64 KB
        with open(path, "rb") as f:
            f.seek(0, 2)
            remaining = f.tell()
            leftover  = b""
            while remaining > 0 and len(buf) < max_lines:
                read_size = min(chunk, remaining)
                remaining -= read_size
                f.seek(remaining)
                data  = f.read(read_size) + leftover
                parts = data.split(b"\n")
                leftover = parts[0]
                for part in reversed(parts[1:]):
                    buf.appendleft(part.decode("utf-8", errors="replace"))
                    if len(buf) >= max_lines:
                        break
            if leftover:
                buf.appendleft(leftover.decode("utf-8", errors="replace"))
        return list(buf)

    raw_lines = tail_file(filepath, MAX_TAIL)

    # ── parse log line ─────────────────────────────────────────────────────────
    LOG_RE = re.compile(
        r"^\[(?P<ts>[^\]]+)\]\s+\[(?P<pid>[^\]]+)\]\s+\[(?P<level>[^\]]+)\]\s+\[(?P<logger>[^\]]+)\]\s+(?P<msg>.*)$"
    )

    def parse_line(raw):
        m = LOG_RE.match(raw)
        if m:
            return {"ts": m.group("ts"), "pid": m.group("pid"),
                    "level": m.group("level"), "logger": m.group("logger"),
                    "msg": m.group("msg"), "raw": raw}
        return {"ts": "", "pid": "", "level": "INFO", "logger": "",
                "msg": raw, "raw": raw}

    parsed = [parse_line(l) for l in raw_lines if l.strip()]

    # ── filter ─────────────────────────────────────────────────────────────────
    if level_filt and level_filt != "ALL":
        parsed = [l for l in parsed if l["level"] == level_filt]
    if search:
        parsed = [l for l in parsed if search in l["raw"].lower()]
    if date_from:
        parsed = [l for l in parsed if l["ts"][:10] >= date_from]
    if date_to:
        parsed = [l for l in parsed if l["ts"][:10] <= date_to]

    # newest first
    parsed.reverse()

    total = len(parsed)
    pages = max(1, -(-total // PER_PAGE))   # ceiling division
    page  = min(page, pages)
    start = (page - 1) * PER_PAGE
    slice_ = parsed[start: start + PER_PAGE]

    return jsonify({
        "lines":     slice_,
        "total":     total,
        "page":      page,
        "pages":     pages,
        "per_page":  PER_PAGE,
        "file_size": file_size,
        "file":      file_key,
        "tailed":    len(raw_lines),   # how many raw lines were read
        "max_tail":  MAX_TAIL,
    })



@app.route("/api/mqtt/broker-logs", methods=["GET"])
def get_mqtt_broker_logs():
    """Get MQTT broker statistics and logs from $SYS/broker topics"""
    try:
        from esp32OTA.Services.mqtt_client import mqtt_service
        
        broker_stats = mqtt_service.broker_stats or {}
        
        # Format broker stats into log-like entries
        logs = []
        
        if broker_stats:
            # Add version info
            if 'version' in broker_stats:
                logs.append({
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'level': 'INFO',
                    'message': f"MQTT Broker Version: {broker_stats['version']}"
                })
            
            # Add uptime
            if 'uptime' in broker_stats:
                logs.append({
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'level': 'INFO',
                    'message': f"Broker Uptime: {broker_stats['uptime']} seconds"
                })
            
            # Add client info
            if 'clients/total' in broker_stats:
                logs.append({
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'level': 'INFO',
                    'message': f"Total Clients: {broker_stats['clients/total']}"
                })
            
            if 'clients/connected' in broker_stats:
                logs.append({
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'level': 'INFO',
                    'message': f"Connected Clients: {broker_stats['clients/connected']}"
                })
            
            # Add subscription info
            if 'subscriptions/count' in broker_stats:
                logs.append({
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'level': 'INFO',
                    'message': f"Active Subscriptions: {broker_stats['subscriptions/count']}"
                })
            
            # Add message stats
            if 'messages/stored' in broker_stats:
                logs.append({
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'level': 'INFO',
                    'message': f"Stored Messages: {broker_stats['messages/stored']}"
                })
            
            if 'messages/received' in broker_stats:
                logs.append({
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'level': 'INFO',
                    'message': f"Total Messages Received: {broker_stats['messages/received']}"
                })

            if 'messages/sent' in broker_stats:
                logs.append({
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'level': 'INFO',
                    'message': f"Total Messages Sent: {broker_stats['messages/sent']}"
                })
            
            # Add publish stats
            if 'publish/messages/received' in broker_stats:
                logs.append({
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'level': 'INFO',
                    'message': f"Published Messages Received: {broker_stats['publish/messages/received']}"
                })
            
            if 'publish/messages/sent' in broker_stats:
                logs.append({
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'level': 'INFO',
                    'message': f"Published Messages Sent: {broker_stats['publish/messages/sent']}"
                })
            
            # Add load info
            if 'load/messages/received/1min' in broker_stats:
                logs.append({
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'level': 'INFO',
                    'message': f"Load (1min): {broker_stats['load/messages/received/1min']} msg/sec received"
                })
            
            if 'load/messages/sent/1min' in broker_stats:
                logs.append({
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'level': 'INFO',
                    'message': f"Load (1min): {broker_stats['load/messages/sent/1min']} msg/sec sent"
                })
        else:
            logs.append({
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'level': 'WARNING',
                'message': 'No MQTT broker statistics available. Ensure MQTT broker is connected.'
            })
        
        return jsonify({
            "logs": logs,
            "total": len(logs),
            "broker_connected": bool(broker_stats)
        })
    
    except Exception as e:
        logger.error(f"Error fetching MQTT broker logs: {str(e)}")
        return jsonify({
            "logs": [{
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'level': 'ERROR',
                'message': f"Error fetching broker logs: {str(e)}"
            }],
            "total": 1,
            "broker_connected": False
        }), 500


app.register_blueprint(users_bp, url_prefix="/api/users")
app.register_blueprint(device_bp, url_prefix="/api/device")
app.register_blueprint(device_type_bp, url_prefix="/api/device-type")
app.register_blueprint(mqtt_auth_bp, url_prefix="/api/mqtt")
app.register_blueprint(firmware_bp, url_prefix="/api/firmware")
app.register_blueprint(gateway_logging_bp, url_prefix="/api/gateway-logging")
app.register_blueprint(api_token_bp, url_prefix="/api/api-tokens")
app.register_blueprint(usage_logging_bp, url_prefix="/api/usage-logging")
app.register_blueprint(ping_logging_bp, url_prefix="/api/ping-logging")