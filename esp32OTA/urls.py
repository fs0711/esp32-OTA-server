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
            last_update = connection.get('last_update', '')
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
            
            if 'messages/received/total' in broker_stats:
                logs.append({
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'level': 'INFO',
                    'message': f"Total Messages Received: {broker_stats['messages/received/total']}"
                })
            
            if 'messages/sent/total' in broker_stats:
                logs.append({
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'level': 'INFO',
                    'message': f"Total Messages Sent: {broker_stats['messages/sent/total']}"
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