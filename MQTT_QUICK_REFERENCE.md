# MQTT Authentication - Quick Reference

## 📋 Overview
HMAC-SHA256 based authentication for ESP32 devices connecting to MQTT broker.

## 🏗️ Architecture
- **Backend**: Gunicorn with dual-binding (Unix socket + localhost:5000)
- **Web Traffic**: Nginx → Unix socket
- **MQTT Auth**: Mosquitto-go-auth → http://127.0.0.1:5000
- **Security**: Port 5000 only accessible from localhost

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for complete architecture details.

## 🔑 Authentication Methods

### 1. File-Based (Local Server Clients)
- **Username**: admin (or custom)
- **Password**: Set via mosquitto_passwd
- **Access**: All topics (#)
- **Setup**: `sudo bash setup_local_mqtt_users.sh`

### 2. HTTP Backend (ESP32 Devices)
- **Username**: Device ID (e.g., `DV-001`)
- **Password**: HMAC-SHA256(access_token, device_id)
- **Algorithm**: HMAC-SHA256

## 📁 Files Created

### Backend Files
- `esp32OTA/DeviceManagement/controllers/MQTTAuthController.py` - Authentication controller
- `esp32OTA/DeviceManagement/views/mqtt_auth.py` - Flask blueprint with 3 endpoints
- Updated `esp32OTA/urls.py` - Registered `/api/mqtt` blueprint

### Configuration Files
- `mosquitto.conf` - Production-ready Mosquitto configuration
- `setup_mosquitto.sh` - Linux/Unix automated setup script
- `setup_mosquitto.bat` - Windows automated setup script

### Testing & Utility Scripts
- `test_mqtt_auth.py` - Comprehensive test suite
- `generate_mqtt_password.py` - HMAC password generator
- `MQTT_AUTH_README.md` - Complete documentation

## 🚀 Quick Start

### 1. Setup Mosquitto Broker
```bash
# Linux
sudo bash setup_mosquitto.sh

# Windows (as Administrator)
setup_mosquitto.bat
```

### 2a. Setup Local Admin User (Server Access)
```bash
# Linux
sudo bash setup_local_mqtt_users.sh

# Windows (as Administrator)
setup_local_mqtt_users.bat
```

### 2b. Generate MQTT Password (Device Access)
```bash
python generate_mqtt_password.py DV-001 <access-token>
```

### 3. Test Connections

**Authenticated Client (Port 1883 - Required):**
```bash
# With credentials
mosquitto_pub -h localhost -u "admin" -P "password" -t "system/test" -m "Hello"
```

**Local Server Client (Port 1884 - Localhost, No Auth):**
```bash
mosquitto_pub -h localhost -p 1884 -t "system/test" -m "Hello"
```

**Anonymous Testing (Port 1885 - DISABLE in Production):**
```bash
mosquitto_pub -h localhost -p 1885 -t "test/topic" -m "Hello"
```

**Device Client (Port 1883 - HMAC Auth):**
```bash
mosquitto_pub -h localhost -u "DV-001" -P "<hmac_password>" \
  -t "devices/DV-001/test" -m "Hello"
```

## 🔌 API Endpoints

### Authentication
```
POST /api/mqtt/auth
Body: username=DV-001&password=<hmac>
Response: 200 if authenticated
```

### Superuser Check
```
POST /api/mqtt/superuser
Body: username=DV-001
Response: is_superuser=false (for devices)
```

### ACL Authorization
```
POST /api/mqtt/acl
Body: username=DV-001&topic=devices/DV-001/data&acc=2
Response: authorized=true/false
```

## 🌐 Connection Ports

### Port 1883 (Standard MQTT)
- **Access**: External and localhost
- **Auth**: Multiple backends (files + HTTP)
- **Use**: Production device connections
- **Clients**: ESP32 devices, authenticated users

### Port 1884 (Localhost Only)
- **Access**: localhost (127.0.0.1) only
- **Auth**: None (anonymous allowed)
- **Use**: Local server applications
- **Clients**: Monitoring tools, admin scripts

## 🔐 HMAC Password Generation

### Python
```python
import hmac, hashlib
password = hmac.new(
    access_token.encode('utf-8'),
    device_id.encode('utf-8'),
    hashlib.sha256
).hexdigest()
```

### ESP32/Arduino (C++)
```cpp
#include "mbedtls/md.h"

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
    
    String result = "";
    for(int i = 0; i < 32; i++) {
        char str[3];
        sprintf(str, "%02x", (int)hmacResult[i]);
        result += str;
    }
    return result;
}

// Usage
String password = generateHMAC(access_token, device_id);
```

## 📝 Mosquitto Configuration

### Key Settings
```conf
# TESTING: Allow both authenticated and anonymous
allow_anonymous true  # Set to false for production

# Backend endpoints
auth_opt_http_host http://localhost
auth_opt_http_port 5000
auth_opt_http_getuser_uri /api/mqtt/auth
auth_opt_http_superuser_uri /api/mqtt/superuser
auth_opt_http_aclcheck_uri /api/mqtt/acl
```Local Server Client (Full Access)
```bash
# Option 1: Localhost port (no auth needed)
mosquitto_pub -h localhost -p 1884 -t "system/test" -m "Hello"
mosquitto_sub -h localhost -p 1884 -t "#" -v

# Option 2: With username/password
mosquitto_pub -h localhost -u "admin" -P "password" -t "system/test" -m "Hello"
mosquitto_sub -h localhost -u "admin" -P "password" -t "#" -v
```

### Device Client (HMAC Authentication)

### Production Checklist
- [ ] Set `allow_anonymous false`
- [ ] Set `auth_opt_log_level error`
- [ ] Enable TLS/SSL
- [ ] Update `auth_opt_http_host` to production URL
- [ ] Use HTTPS for backend
- [ ] Configure firewall rules
- [ ] Set up log rotation
- [ ] Test ACL rules

## 🧪 Testing Commands

### Test with mosquitto_pub/sub
```bash
# Generate password first
python generate_mqtt_password.py DV-001 <token>

# Publish
mosquitto_pub -h localhost -u "DV-001" -P "<password>" \
  -t "devices/DV-001/telemetry" -m '{"temp":25.5}'

# Subscribe
mosquitto_sub -h localhost -u "DV-001" -P "<password>" \
  -t "devices/DV-001/#"

# Test anonymous (while allow_anonymous=true)
mosquitto_pub -h localhost -t "test/topic" -m "Anonymous message"
```

### Test with curl
```bash
# Authentication
curl -X POST http://localhost:5000/api/mqtt/auth \
  -d "username=DV-001&password=<hmac>"

# ACL
curl -X POST http://localhost:5000/api/mqtt/acl \
  -d "username=DV-001&topic=devices/DV-001/data&acc=2"
```

### Test with Python script
```bash
# Full test suite
python test_mqtt_auth.py --device-id DV-001 --access-token <token>

# Specific tests
python test_mqtt_auth.py --device-id DV-001 --access-token <token> \
  --skip-acl --skip-superuser
```

## 🔍 Troubleshooting

### Check Mosquitto Status
```bash
# Linux
sudo systemctl status mosquitto
sudo journalctl -u mosquitto -f

# Windows
sc query mosquitto
```

### Common Issues

**Authentication fails:**
- Verify device exists in database
- Check device status is "active"
- Verify access_token matches
- Check HMAC password generation

**Connection refused:**
- Check Mosquitto is running
- Verify port 1883 is open
- Check firewall rules

**ACL denies access:**
- Topic must contain device_id
- Review ACL rules in MQTTAuthController

**Backend unreachable:**
- Verify backend is running
- Check `auth_opt_http_host` and `auth_opt_http_port`
- Review backend logs

### Enable Debug Logging
Edit `mosquitto.conf`:
```conf
auth_opt_log_level debug
log_type all
```
Restart Mosquitto and check logs.

## 📚 Additional Resources

- **Full Documentation**: [MQTT_AUTH_README.md](MQTT_AUTH_README.md)
- **Mosquitto Config**: [mosquitto.conf](mosquitto.conf)
- **mosquitto-go-auth**: https://github.com/iegomez/mosquitto-go-auth
- **Mosquitto Docs**: https://mosquitto.org/documentation/

## 🔒 Security Notes

1. **Always use TLS in production**
2. **Disable anonymous access** (`allow_anonymous false`)
3. **Use HTTPS for backend** communication
4. **Rotate access tokens** periodically
5. **Monitor authentication logs**
6. **Implement rate limiting**
7. **Review ACL rules** regularly
8. **Keep software updated**

## 📞 Support

For issues or questions:
1. Check logs: `journalctl -u mosquitto -f`
2. Test endpoints: `python test_mqtt_auth.py`
3. Review configuration: `mosquitto.conf`
4. Check backend status: `/api/static-data`
