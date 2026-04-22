# Local MQTT Client Connection Guide
## Full Access for Server Applications

## 🎯 Overview

This guide shows how to connect local server applications to the MQTT broker with full access to all topics. This is useful for:
- Monitoring dashboards
- Data logging services
- Administrative scripts
- Testing and debugging

## 🔌 Connection Options

### Option 1: Localhost-Only Port (Simplest - No Authentication)

**Port**: 1884  
**Access**: Localhost only (127.0.0.1)  
**Authentication**: None required  
**Topics**: Full access to all topics

```bash
# Publish
mosquitto_pub -h localhost -p 1884 -t "system/test" -m "Hello"

# Subscribe to all topics
mosquitto_sub -h localhost -p 1884 -t "#" -v

# Subscribe to device topics
mosquitto_sub -h localhost -p 1884 -t "devices/#" -v
```

**Python Example:**
```python
import paho.mqtt.client as mqtt

client = mqtt.Client()
client.connect("localhost", 1884, 60)

# Publish
client.publish("system/status", "online")

# Subscribe
def on_message(client, userdata, msg):
    print(f"{msg.topic}: {msg.payload.decode()}")

client.on_message = on_message
client.subscribe("#")
client.loop_forever()
```

### Option 2: File-Based Authentication (More Secure - Port 1883)

**Port**: 1883 (standard MQTT port)  
**Access**: Localhost or remote  
**Authentication**: Username/password (REQUIRED)  
**Topics**: Full access (superuser)

#### Setup

**Linux:**
```bash
sudo bash setup_local_mqtt_users.sh
```

**Windows (as Administrator):**
```cmd
setup_local_mqtt_users.bat
```

This creates:
- User: `admin` (or custom name)
- Password: Your chosen password
- Access: All topics with read/write

#### Usage

```bash
# Publish to any topic
mosquitto_pub -h localhost -u "admin" -P "yourpassword" \
  -t "system/alerts" -m "Server started"

# Subscribe to all topics
mosquitto_sub -h localhost -u "admin" -P "yourpassword" \
  -t "#" -v

# Subscribe to specific pattern
mosquitto_sub -h localhost -u "admin" -P "yourpassword" \
  -t "devices/+/telemetry" -v
```

**Python Example:**
```python
import paho.mqtt.client as mqtt

client = mqtt.Client()
client.username_pw_set("admin", "yourpassword")
client.connect("localhost", 1883, 60)

# Rest is same as Option 1
```

## 📊 Use Cases

### 1. Real-Time Monitoring Dashboard

```python
import paho.mqtt.client as mqtt
import json
from datetime import datetime

def on_message(client, userdata, msg):
    data = {
        'timestamp': datetime.now().isoformat(),
        'topic': msg.topic,
        'payload': msg.payload.decode()
    }
    print(json.dumps(data, indent=2))

client = mqtt.Client()
client.on_message = on_message

# Option 1: No auth (port 1884)
client.connect("localhost", 1884, 60)

# Option 2: With auth (port 1883)
# client.username_pw_set("admin", "password")
# client.connect("localhost", 1883, 60)

client.subscribe("devices/#")
client.loop_forever()
```

### 2. Data Logger

```python
import paho.mqtt.client as mqtt
import csv
from datetime import datetime

# Open CSV file
log_file = open('mqtt_log.csv', 'a', newline='')
csv_writer = csv.writer(log_file)

def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")
    client.subscribe("#")  # Subscribe to everything

def on_message(client, userdata, msg):
    timestamp = datetime.now().isoformat()
    csv_writer.writerow([timestamp, msg.topic, msg.payload.decode()])
    log_file.flush()

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

# Connect to localhost port (no auth)
client.connect("localhost", 1884, 60)
client.loop_forever()
```

### 3. Device Command Broadcaster

```python
import paho.mqtt.client as mqtt
import sys

def send_command(device_id, command):
    client = mqtt.Client()
    
    # Use localhost port for admin access
    client.connect("localhost", 1884, 60)
    
    topic = f"devices/{device_id}/commands"
    client.publish(topic, command)
    print(f"Sent '{command}' to {topic}")
    
    client.disconnect()

# Usage
if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python script.py <device_id> <command>")
        sys.exit(1)
    
    device_id = sys.argv[1]
    command = sys.argv[2]
    send_command(device_id, command)
```

### 4. Health Check Monitor

```python
import paho.mqtt.client as mqtt
import time
from collections import defaultdict

# Track device activity
device_last_seen = defaultdict(lambda: 0)

def on_message(client, userdata, msg):
    # Extract device ID from topic (e.g., devices/DV-001/telemetry)
    parts = msg.topic.split('/')
    if len(parts) >= 2 and parts[0] == 'devices':
        device_id = parts[1]
        device_last_seen[device_id] = time.time()

def check_health():
    """Check which devices haven't reported in last 5 minutes"""
    now = time.time()
    threshold = 300  # 5 minutes
    
    print("\n=== Device Health Status ===")
    for device_id, last_seen in device_last_seen.items():
        age = now - last_seen
        status = "ONLINE" if age < threshold else "OFFLINE"
        print(f"{device_id}: {status} (last seen {int(age)}s ago)")

client = mqtt.Client()
client.on_message = on_message
client.connect("localhost", 1884, 60)
client.subscribe("devices/+/telemetry")

# Start loop in background
client.loop_start()

# Periodic health checks
try:
    while True:
        time.sleep(60)
        check_health()
except KeyboardInterrupt:
    client.loop_stop()
    client.disconnect()
```

## 🔒 Security Considerations

### Port 1884 (Localhost Only)
✅ **Pros:**
- No authentication needed
- Simple to use
- Fast for local scripts

⚠️ **Cons:**
- Only accessible from localhost
- No audit trail of who published what
- Cannot be used remotely

**Best for:** Development, testing, local monitoring

### Port 1883 (File-Based Auth)
✅ **Pros:**
- Username/password authentication
- Can be used remotely (with firewall rules)
- Audit trail in logs
- Can create multiple users with different permissions

⚠️ **Cons:**
- Requires password management
- Slightly more complex setup

**Best for:** Production monitoring, remote access, multi-user scenarios

## 📝 Topic Recommendations

### Recommended Structure
```
system/
  ├─ status         - System-wide status
  ├─ alerts         - Critical alerts
  └─ logs           - System logs

devices/
  └─ {device_id}/
      ├─ telemetry  - Sensor data
      ├─ commands   - Control commands
      ├─ status     - Device status
      ├─ config     - Configuration
      └─ logs       - Device logs

admin/
  ├─ commands       - Admin commands
  └─ notifications  - Admin notifications
```

### Subscribing Patterns
```bash
# All device telemetry
mosquitto_sub -h localhost -p 1884 -t "devices/+/telemetry" -v

# All topics for specific device
mosquitto_sub -h localhost -p 1884 -t "devices/DV-001/#" -v

# All system topics
mosquitto_sub -h localhost -p 1884 -t "system/#" -v

# Everything
mosquitto_sub -h localhost -p 1884 -t "#" -v
```

## 🧪 Testing

```bash
# Terminal 1: Subscribe to all topics
mosquitto_sub -h localhost -p 1884 -t "#" -v

# Terminal 2: Publish test messages
mosquitto_pub -h localhost -p 1884 -t "system/test" -m "Test 1"
mosquitto_pub -h localhost -p 1884 -t "devices/DV-001/telemetry" -m '{"temp":25.5}'
mosquitto_pub -h localhost -p 1884 -t "admin/commands" -m "restart"
```

## 🔧 User Management

### Add New User
```bash
# Linux
sudo mosquitto_passwd /etc/mosquitto/auth/passwords newuser

# Windows
mosquitto_passwd C:\Program Files\mosquitto\auth\passwords newuser
```

### Delete User
```bash
# Linux
sudo mosquitto_passwd -D /etc/mosquitto/auth/passwords olduser

# Windows
mosquitto_passwd -D C:\Program Files\mosquitto\auth\passwords olduser
```

### List All Users
```bash
# Linux
cut -d: -f1 /etc/mosquitto/auth/passwords

# Windows (PowerShell)
Get-Content "C:\Program Files\mosquitto\auth\passwords" | ForEach-Object { ($_ -split ':')[0] }
```

### Update ACL (Access Control)
Edit `/etc/mosquitto/auth/acl` (Linux) or `C:\Program Files\mosquitto\auth\acl` (Windows):

```conf
# Full access
user admin
topic readwrite #

# Read-only monitoring
user monitor
topic read #

# Limited to system topics
user sysadmin
topic readwrite system/#
topic read devices/#
```

After changes, restart Mosquitto:
```bash
sudo systemctl restart mosquitto
```

## 📚 Additional Resources

- [MQTT_AUTH_README.md](MQTT_AUTH_README.md) - Complete authentication guide
- [MQTT_QUICK_REFERENCE.md](MQTT_QUICK_REFERENCE.md) - Quick command reference
- [mosquitto_acl.conf](mosquitto_acl.conf) - ACL configuration example
- [Paho MQTT Python](https://pypi.org/project/paho-mqtt/) - Python MQTT client library
