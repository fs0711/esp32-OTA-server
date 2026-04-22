# MQTT Connection Summary
## ESP32 OTA Backend

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          MQTT BROKER ARCHITECTURE                        │
└─────────────────────────────────────────────────────────────────────────┘

                         MOSQUITTO MQTT BROKER
                    ┌──────────────────────────────┐
                    │   Dual Authentication        │
                    │   Backend Support            │
                    └──────────────┬───────────────┘
                                   │
                    ┌──────────────┴───────────────┐
                    │                              │
            ┌───────▼────────┐           ┌────────▼───────┐
            │ FILES BACKEND  │           │ HTTP BACKEND   │
            │  (local users) │           │  (ESP32 HMAC)  │
            └───────┬────────┘           └────────┬───────┘
                    │                             │
        ┌───────────┴───────────┐    ┌────────────┴──────────┐
        │                       │    │                       │
   ┌────▼────┐           ┌─────▼────▼──┐           ┌───────▼────┐
   │Port 1884│           │  Port 1883  │           │   Flask    │
   │localhost│           │   0.0.0.0   │           │   Backend  │
   │ No Auth │           │Multi Backend│           │127.0.0.1:5K│
   └────┬────┘           └─────┬───────┘           └────────────┘
        │                      │
        │                      ├─────────────┬─────────────┬──────────
        │                      │             │             │
   ┌────▼────────┐   ┌─────────▼──┐   ┌─────▼──┐   ┌──────▼───┐
   │   Local     │   │   Admin    │   │ Device │   │Anonymous │
   │  Scripts    │   │   User     │   │ (HMAC) │   │ (Testing)│
   │(monitoring) │   │(user/pass) │   │        │   │          │
   └─────────────┘   └────────────┘   └────────┘   └──────────┘
```

## 🔌 Connection Matrix

| Client Type | Port | Auth Method | Topics Access | Use Case |
|-------------|------|-------------|---------------|----------|
| **ESP32 Device** | 1883 | HMAC-SHA256 | Device-specific | IoT devices, firmware updates |
| **Admin User** | 1883 | Username/Password | All (#) | Remote admin, dashboards |
| **Local Scripts** | 1884 | None | All (#) | Server monitoring (localhost only) |
| **Testing/Dev** | 1885 | None | All (#) | Quick testing (DISABLE in production) |

## 📁 File Locations

### Linux
```
/etc/mosquitto/
├── mosquitto.conf           # Main configuration
└── auth/
    ├── passwords            # Local user passwords (hashed)
    └── acl                  # Access Control List

/var/log/mosquitto/          # Log files (if file logging)
/var/lib/mosquitto/          # Persistence storage
```

### Windows
```
C:\Program Files\mosquitto\
├── mosquitto.conf           # Main configuration
├── mosquitto-go-auth.dll    # Auth plugin
└── auth\
    ├── passwords            # Local user passwords (hashed)
    └── acl                  # Access Control List
```

## 🎯 Quick Connection Examples

### 1. Local Server Monitoring (Easiest)
```bash
# No authentication needed
mosquitto_sub -h localhost -p 1884 -t "devices/#" -v
```

### 2. Admin Dashboard (Secure)
```bash
# With username/password
mosquitto_sub -h localhost -u admin -P password -t "#" -v
```

### 3. ESP32 Device (HMAC)
```python
import paho.mqtt.client as mqtt
import hmac, hashlib

device_id = "DV-001"
access_token = "your-token"
password = hmac.new(access_token.encode(), device_id.encode(), hashlib.sha256).hexdigest()

client = mqtt.Client()
client.username_pw_set(device_id, password)
client.connect("mqtt.example.com", 1883, 60)
```

## 🔒 Security Levels

```
┌─────────────────────────────────────────────────────────┐
│ Security Level          │ Port │ Auth  │ Recommended  │
├─────────────────────────┼──────┼───────┼──────────────┤
│ Localhost Only (dev)    │ 1884 │ None  │ Development  │
│ File-based (user/pass)  │ 1883 │ Files │ Production   │
│ HMAC Device Auth        │ 1883 │ HTTP  │ Production   │
│ Anonymous (testing)     │ 1883 │ None  │ Testing Only │
└─────────────────────────────────────────────────────────┘
```

## 📊 Authentication Flow

### Local User (Files Backend)
```
Client → Mosquitto → Files Backend → /etc/mosquitto/auth/passwords
                   ↓
              Check Password Hash
                   ↓
              /etc/mosquitto/auth/acl
                   ↓
              Grant Access
```

### ESP32 Device (HTTP Backend)
```
Device → Mosquitto → HTTP Backend → Flask API (127.0.0.1:5000)
                   ↓                         ↓
              Check HMAC            Query Database
                   ↓                         ↓
              ACL Check             Check device_id & token
                   ↓                         ↓
              Grant Access          Return auth result
```

## 🚀 Setup Commands Summary

```bash
# 1. Install and configure Mosquitto
sudo bash setup_mosquitto.sh

# 2. Create local admin users
sudo bash setup_local_mqtt_users.sh

# 3. Generate device HMAC passwords
python generate_mqtt_password.py DV-001 <token>

# 4. Test connections
python test_mqtt_auth.py --device-id DV-001 --access-token <token>

# 5. Verify deployment
sudo bash verify_deployment.sh

# 6. Monitor logs
journalctl -u mosquitto -f
```

## 📚 Documentation Files

| File | Description |
|------|-------------|
| [mosquitto.conf](mosquitto.conf) | Complete broker configuration |
| [MQTT_AUTH_README.md](MQTT_AUTH_README.md) | Full authentication guide |
| [LOCAL_MQTT_CLIENTS.md](LOCAL_MQTT_CLIENTS.md) | Local client setup and examples |
| [MQTT_QUICK_REFERENCE.md](MQTT_QUICK_REFERENCE.md) | Command quick reference |
| [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) | Production deployment guide |
| [mosquitto_acl.conf](mosquitto_acl.conf) | ACL configuration template |

## 🔧 Management Commands

```bash
# User Management
mosquitto_passwd /etc/mosquitto/auth/passwords username    # Add/update user
mosquitto_passwd -D /etc/mosquitto/auth/passwords username # Delete user
cut -d: -f1 /etc/mosquitto/auth/passwords                  # List users

# Service Management
sudo systemctl start mosquitto      # Start service
sudo systemctl stop mosquitto       # Stop service
sudo systemctl restart mosquitto    # Restart service
sudo systemctl status mosquitto     # Check status

# Monitoring
journalctl -u mosquitto -f          # Follow logs
journalctl -u mosquitto -n 100      # Last 100 lines
mosquitto_sub -h localhost -p 1884 -t "#" -v  # Monitor all topics
```

## ⚠️ Production Checklist

- [ ] Set `allow_anonymous false` in mosquitto.conf
- [ ] Enable TLS/SSL on port 8883
- [ ] Configure firewall (allow 1883, 8883; block 1884, 5000)
- [ ] Set strong passwords for admin users
- [ ] Review and restrict ACL permissions
- [ ] Set log level to `warning` or `error`
- [ ] Enable log rotation
- [ ] Regular password updates
- [ ] Monitor authentication failures
- [ ] Backup password and ACL files
