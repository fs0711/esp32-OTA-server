# MQTT Authentication Endpoint Documentation

## Overview
This endpoint provides HMAC-based authentication for MQTT clients (ESP32 devices). The authentication uses the device's access_token as the HMAC secret key and the device_id as the username.

## ⚙️ Deployment Architecture

The backend uses **dual-binding mode** with Gunicorn to support both web traffic (via Nginx) and MQTT authentication:

- **Nginx Reverse Proxy** → `unix:esp32ota.sock` (web traffic)
- **Mosquitto-go-auth** → `http://127.0.0.1:5000` (MQTT authentication)

This setup ensures:
- ✅ Nginx continues to use efficient Unix socket communication
- ✅ MQTT auth plugin can make HTTP requests to localhost
- ✅ Port 5000 is only accessible from localhost (secure)
- ✅ No external exposure of the backend port

**Important:** Mosquitto must run on the **same server** as the backend. See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for complete setup instructions.

## 🔐 Authentication Methods

Mosquitto supports **two authentication backends** simultaneously:

### 1. File-Based Authentication (Local Server Clients)
- **Purpose**: Local admin users, monitoring tools, server scripts
- **Access**: Full access to all topics (superuser)
- **Credentials**: Username/password stored in `/etc/mosquitto/auth/passwords`
- **Setup**: Run `setup_local_mqtt_users.sh` (Linux) or `setup_local_mqtt_users.bat` (Windows)

**Use Cases:**
- Server monitoring dashboards
- Administrative scripts
- Data logging services
- Testing and debugging

### 2. HTTP Backend Authentication (ESP32 Devices)
- **Purpose**: IoT devices (ESP32)
- **Access**: Limited to device-specific topics
- **Credentials**: HMAC-SHA256 signature using device access_token
- **Setup**: Automatically works when device is created via API

**Use Cases:**
- ESP32 firmware updates
- Device telemetry
- Device commands and control

## Endpoints

### 1. Authentication Endpoint
**URL:** `/api/mqtt/auth`  
**Method:** `POST`  
**Content-Type:** `application/x-www-form-urlencoded` or `application/json`

**Request Parameters:**
- `username` (required): The device_id (e.g., "DV-001")
- `password` (required): HMAC-SHA256 signature (hexdigest)

**Response:**
```json
{
    "response_code": 200,
    "response_message": "Authentication successful",
    "response_data": {
        "device_id": "DV-001",
        "name": "Device Name",
        "authenticated": true
    }
}
```

### 2. Superuser Endpoint
**URL:** `/api/mqtt/superuser`  
**Method:** `POST`

**Request Parameters:**
- `username` (required): The device_id

**Response:**
```json
{
    "response_code": 200,
    "response_message": "Not a superuser",
    "response_data": {
        "is_superuser": false
    }
}
```

### 3. ACL (Access Control List) Endpoint
**URL:** `/api/mqtt/acl`  
**Method:** `POST`

**Request Parameters:**
- `username` (required): The device_id
- `topic` (required): MQTT topic to check access for
- `acc` (optional): Access type (1 = subscribe, 2 = publish)
- `clientid` (optional): MQTT client ID

**Response:**
```json
{
    "response_code": 200,
    "response_message": "Access authorized",
    "response_data": {
        "authorized": true
    }
}
```

## How HMAC Authentication Works

### Secret Key
The **access_token** field from the Device model is used as the HMAC secret key. This token is generated when a device is created.

### HMAC Signature Generation
The password should be an HMAC-SHA256 signature computed as follows:

```python
import hmac
import hashlib

# Get these values from the device record
device_id = "DV-001"  # username
access_token = "abc123-secret-token"  # HMAC secret key

# Compute HMAC signature
signature = hmac.new(
    access_token.encode('utf-8'),
    device_id.encode('utf-8'),
    hashlib.sha256
).hexdigest()

# Use this signature as the password
print(f"Password (HMAC): {signature}")
```

### ESP32 Example (Arduino/C++)
```cpp
#include <WiFi.h>
#include <PubSubClient.h>
#include "mbedtls/md.h"

const char* device_id = "DV-001";
const char* access_token = "abc123-secret-token";

String generateHMAC(String key, String message) {
    byte hmacResult[32];
    
    mbedtls_md_context_t ctx;
    mbedtls_md_type_t md_type = MBEDTLS_MD_SHA256;
    
    mbedtls_md_init(&ctx);
    mbedtls_md_setup(&ctx, mbedtls_md_info_from_type(md_type), 1);
    mbedtls_md_hmac_starts(&ctx, (const unsigned char*)key.c_str(), key.length());
    mbedtls_md_hmac_update(&ctx, (const unsigned char*)message.c_str(), message.length());
    mbedtls_md_hmac_finish(&ctx, hmacResult);
    mbedtls_md_free(&ctx);
    
    String hmacString = "";
    for(int i = 0; i < 32; i++) {
        char str[3];
        sprintf(str, "%02x", (int)hmacResult[i]);
        hmacString += str;
    }
    
    return hmacString;
}

void setup() {
    Serial.begin(115200);
    
    // Generate HMAC password
    String password = generateHMAC(String(access_token), String(device_id));
    
    Serial.println("MQTT Credentials:");
    Serial.println("Username: " + String(device_id));
    Serial.println("Password: " + password);
    
    // Use these credentials with your MQTT client
    // client.setCredentials(device_id, password.c_str());
}
```

## MQTT Broker Configuration

### Quick Setup with mosquitto-go-auth

A complete, production-ready configuration file is provided: **[mosquitto.conf](mosquitto.conf)**

This configuration file includes:
- ✅ HTTP backend authentication setup
- ✅ Anonymous access enabled for testing (can be disabled)
- ✅ Detailed comments and production deployment notes
- ✅ Optional TLS/SSL configuration
- ✅ WebSocket support configuration
- ✅ Performance tuning settings

**Quick Start:**

**Automated Setup (Recommended):**
```bash
# Linux/Unix
sudo bash setup_mosquitto.sh

# Windows (Run as Administrator)
setup_mosquitto.bat
```

**Manual Setup:**
```bash
# 1. Install Mosquitto and mosquitto-go-auth plugin
sudo apt-get install mosquitto

# 2. Download and install mosquitto-go-auth
# See: https://github.com/iegomez/mosquitto-go-auth

# 3. Copy the configuration file
sudo cp mosquitto.conf /etc/mosquitto/mosquitto.conf

# 4. Update the backend URL in the config file
sudo nano /etc/mosquitto/mosquitto.conf
# Change: auth_opt_http_host and auth_opt_http_port

# 5. Restart Mosquitto
sudo systemctl restart mosquitto

# 6. Check status
sudo systemctl status mosquitto
```

**Important Configuration Options:**

```conf
# Testing mode - allows both authenticated and anonymous connections
allow_anonymous true  # Set to false for production

# Authentication endpoints
auth_opt_http_host http://localhost
auth_opt_http_port 5000
auth_opt_http_getuser_uri /api/mqtt/auth
auth_opt_http_superuser_uri /api/mqtt/superuser
auth_opt_http_aclcheck_uri /api/mqtt/acl
```

### Using with EMQX
Configure EMQX HTTP authentication:

```hocon
authentication {
  backend = "http"
  mechanism = "password_based"
  method = "post"
  url = "http://your-backend-host:5000/api/mqtt/auth"
  headers {
    "Content-Type" = "application/x-www-form-urlencoded"
  }
  body {
    username = "${username}"
    password = "${password}"
  }
}
```

## ACL Rules

The current ACL implementation allows devices to publish/subscribe to topics that contain their device_id. You can customize the ACL logic in `MQTTAuthController.authorize_mqtt_acl_controller()`.

**Example:**
- Device `DV-001` can access topics like:
  - `devices/DV-001/telemetry`
  - `devices/DV-001/commands`
  - `DV-001/status`

## Security Considerations

1. **Use TLS/SSL**: Always use encrypted connections (MQTT over TLS) in production
2. **Secure the Backend**: Ensure the backend API is only accessible from the MQTT broker
3. **Token Rotation**: Implement token rotation for enhanced security
4. **Rate Limiting**: Add rate limiting to prevent brute force attacks
5. **Logging**: Monitor authentication attempts for suspicious activity

## Testing

### Using the Test Script (Recommended)

A comprehensive test script is provided: **[test_mqtt_auth.py](test_mqtt_auth.py)**

```bash
# Install required package
pip install requests

# Run complete test suite
python test_mqtt_auth.py --device-id DV-001 --access-token <your-device-access-token>

# Test specific endpoint
python test_mqtt_auth.py --device-id DV-001 --access-token <token> --skip-acl --skip-superuser

# Use custom backend URL
python test_mqtt_auth.py --device-id DV-001 --access-token <token> --base-url http://192.168.1.100:5000
```

### Generate HMAC Password

Use the password generator: **[generate_mqtt_password.py](generate_mqtt_password.py)**

```bash
# Simple usage
python generate_mqtt_password.py DV-001 <access-token>

# JSON output
python generate_mqtt_password.py --device-id DV-001 --access-token <token> --format json

# Environment variables format
python generate_mqtt_password.py --device-id DV-001 --access-token <token> --format env
```

### Using curl:
```bash
# Test authentication
curl -X POST http://localhost:5000/api/mqtt/auth \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=DV-001&password=<hmac_signature>"

# Test ACL
curl -X POST http://localhost:5000/api/mqtt/acl \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=DV-001&topic=devices/DV-001/telemetry&acc=2"
```

### Using Python:
```python
import requests
import hmac
import hashlib

# Device credentials
device_id = "DV-001"
access_token = "abc123-secret-token"

# Generate HMAC password
password = hmac.new(
    access_token.encode('utf-8'),
    device_id.encode('utf-8'),
    hashlib.sha256
).hexdigest()

# Test authentication
response = requests.post(
    'http://localhost:5000/api/mqtt/auth',
    data={
        'username': device_id,
        'password': password
    }
)

print(response.json())
```