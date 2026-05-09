# ZVOLTA - IoT Gateway Management System

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-green.svg)
![Flask](https://img.shields.io/badge/flask-2.0+-orange.svg)
![License](https://img.shields.io/badge/license-MIT-brightgreen.svg)

A comprehensive IoT Gateway Management System built with Flask and MongoDB, designed for managing smart devices, firmware updates, MQTT broker integration, and real-time system monitoring.

---

## 📋 Table of Contents

- [Features](#-features)
- [System Architecture](#-system-architecture)
- [Project Structure](#-project-structure)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage](#-usage)
- [API Documentation](#-api-documentation)
- [Database](#-database-schema)
- [MQTT Integration](#-mqtt-integration)
- [Deployment](#-deployment)
- [Troubleshooting](#-troubleshooting)

---

## ✨ Features

### Core Features
- **🔐 User Authentication**: Secure login with token-based authentication
- **📱 Device Management**: Register, monitor, and manage IoT devices
- **⚙️ Firmware Management**: Upload and manage device firmware versions
- **📊 Real-time Dashboard**: Live device status monitoring with MQTT metrics
- **🔔 Notifications**: System alerts and notifications for device events
- **📝 System Logging**: Comprehensive application and MQTT broker logging
- **🎮 Device Type Management**: Define and manage different device types
- **🔑 MQTT Authentication**: Secure MQTT broker access control

### Advanced Features
- **📡 Live MQTT Broker Monitoring**: Real-time broker statistics and health metrics
- **🔄 Device Heartbeat System**: Automatic device status tracking
- **📅 Scheduled Tasks**: Background job scheduling for automation
- **🔗 Token Management**: JWT-like token system for secure API access
- **📤 File Upload Support**: Upload firmware files and device configurations
- **🌐 CORS Support**: Cross-origin resource sharing for web clients
- **🔍 API Documentation**: Interactive Swagger-like API explorer

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Web Browsers / Clients                      │
└──────────────┬──────────────────────────────────────────────────┘
               │ HTTP/HTTPS
               ↓
┌─────────────────────────────────────────────────────────────────┐
│                    Flask Web Application                         │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Routes & Views                                             │ │
│  ├─ User Management (Login, Register, Profile)               │ │
│  ├─ Device Management (CRUD operations)                      │ │
│  ├─ Firmware Management (Upload, Deploy)                     │ │
│  ├─ Gateway Dashboard (Real-time monitoring)                 │ │
│  ├─ API Documentation (Swagger-like interface)               │ │
│  └─ System Logs (Application & MQTT logs)                    │ │
│  └────────────────────────────────────────────────────────────┘ │
└──────┬──────────────────────────────────┬──────────────────────┘
       │                                  │
       ↓                                  ↓
   MongoDB                           MQTT Broker
   (Data Store)                      (Mosquitto)
       │                                  │
       └──────────────────┬───────────────┘
                          ↓
                   IoT Devices
              (ESP32, sensors, etc.)
```

---

## 📂 Project Structure

```
ZVOLTA/
├── app.py                              # Flask app entry point
├── wsgi.py                             # WSGI server entry point
├── gunicorn.conf.py                    # Gunicorn configuration
├── requirements.txt                    # Python dependencies
├── mosquitto.conf                      # MQTT broker configuration
├── esp32OTA/
│   ├── __init__.py                    # Flask app initialization
│   ├── urls.py                        # Route definitions
│   ├── config/
│   │   ├── config.py                  # Configuration management
│   │   └── static/
│   │       └── static_data.json       # Static data constants
│   ├── generic/
│   │   ├── database.py                # MongoDB connection
│   │   ├── models.py                  # Base models
│   │   ├── controllers.py             # Base controllers
│   │   └── services/
│   │       ├── messages/
│   │       │   └── message.py        # Message formatting
│   │       └── utils/
│   │           ├── constants.py       # Application constants
│   │           ├── decorators.py      # Custom decorators
│   │           ├── common_utils.py    # Utility functions
│   │           ├── response_codes.py  # HTTP response codes
│   │           ├── response_utils.py  # Response formatting
│   │           ├── validate_data.py   # Data validation
│   │           └── pipeline.py        # Data processing pipeline
│   ├── UserManagement/
│   │   ├── models/User.py            # User model
│   │   ├── controllers/UserController.py
│   │   └── views/users.py            # User endpoints
│   ├── DeviceManagement/
│   │   ├── models/
│   │   │   ├── Device.py             # Device model
│   │   │   └── DeviceType.py         # Device type model
│   │   ├── controllers/
│   │   │   ├── DeviceController.py
│   │   │   ├── DeviceTypeController.py
│   │   │   └── MQTTAuthController.py
│   │   └── views/
│   │       ├── device.py             # Device endpoints
│   │       ├── device_type.py
│   │       └── mqtt_auth.py
│   ├── FirmwareManagement/
│   │   ├── models/Firmware.py        # Firmware model
│   │   ├── controllers/FirmwareController.py
│   │   └── views/firmware.py
│   ├── GatewayLogging/
│   │   ├── models/GatewayLogging.py
│   │   ├── controllers/GatewayLoggingController.py
│   │   └── views/gateway_logging.py
│   ├── NotificationManagement/
│   │   ├── model/Notifications.py
│   │   ├── controller/NotificationsController.py
│   │   └── view/notifications.py
│   ├── TokenManagement/
│   │   ├── models/Token.py
│   │   ├── controllers/TokenController.py
│   │   └── views/tokens.py
│   ├── Logging/
│   │   ├── models/Logging.py
│   │   └── controllers/LoggingController.py
│   ├── Services/
│   │   ├── mqtt_client.py            # MQTT client service
│   │   ├── GatewayService.py         # Gateway business logic
│   │   ├── ConfigController.py       # Configuration service

│   ├── scheduler.py                   # Background task scheduler
│   ├── scheduled_tasks.py            # Scheduled jobs
│   ├── scripts/
│   │   └── First_Admin_User.py       # Admin user creation script
│   └── templates/
│       ├── login.html                # Login page
│       ├── index.html                # Gateway dashboard
│       ├── api_docs.html             # API documentation
│       └── logs.html                 # Logs viewer
├── firmware_files/                    # Uploaded firmware storage
├── mosquitto_acl.conf                # MQTT ACL configuration
├── esp32-ota.service                 # Systemd service file
├── newrelic.ini                      # New Relic monitoring config
└── TODO                              # Project tasks

```

---

## 🚀 Installation

### Prerequisites
- Python 3.8+
- MongoDB 4.0+
- Mosquitto MQTT Broker
- pip (Python package manager)
- Git

### Step 1: Clone Repository
```bash
git clone https://github.com/yourusername/zvolta.git
cd zvolta
```

### Step 2: Create Virtual Environment
```bash
# On Linux/Mac
python3 -m venv venv
source venv/bin/activate

# On Windows
python -m venv venv
venv\Scripts\activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment
```bash
cp config.example.py esp32OTA/config/config.py
# Edit config.py with your settings
```

### Step 5: Initialize Database
```bash
# This will create admin user and initialize collections
python app.py
```

### Step 6: Start MQTT Broker
```bash
# On Linux
sudo systemctl start mosquitto

# On Windows or standalone
mosquitto -c mosquitto.conf
```

### Step 7: Run Application
```bash
# Development
python app.py

# Production with Gunicorn
gunicorn --config gunicorn.conf.py wsgi:app
```

---

## ⚙️ Configuration

### Main Configuration File: `esp32OTA/config/config.py`

```python
# Database
MONGO_DB_URI = "mongodb://localhost:27017/zvolta"

# MQTT Broker
MQTT_BROKER_HOST = "localhost"
MQTT_BROKER_PORT = 1883
MQTT_BROKER_USERNAME = "mqtt_user"
MQTT_BROKER_PASSWORD = "secure_password"

# Flask
SECRET_KEY = "your-secret-key-change-this"
DEBUG = False

# Email (for notifications)
MAIL_SERVER = "smtp.gmail.com"
MAIL_PORT = 587
MAIL_USERNAME = "your-email@gmail.com"
MAIL_PASSWORD = "your-password"

# File Upload
MAX_UPLOAD_SIZE = 100 * 1024 * 1024  # 100MB
ALLOWED_EXTENSIONS = {'bin', 'hex', 'elf'}

# API
API_TIMEOUT = 30
API_RATE_LIMIT = 1000  # per hour

# Logging
LOG_LEVEL = "INFO"
LOG_FILE = "/var/log/zvolta/app.log"
```

### MQTT Configuration: `mosquitto.conf`

```conf
listener 1883
protocol mqtt

listener 9001
protocol websockets

# Authentication
allow_anonymous false
password_file /etc/mosquitto/pwfile

# ACL
acl_file /etc/mosquitto/acl.conf

# Persistence
persistence true
persistence_location /var/lib/mosquitto/
```

---

## 💻 Usage

### Web Interface

#### 1. **Login Page** (`/`)
- Email-based authentication
- Secure password handling
- Token storage in localStorage
- Auto-redirect to dashboard if already logged in

#### 2. **Gateway Dashboard** (`/gateway`)
4 main tabs:

**Overview Tab:**
- MQTT connection status
- Connected device count
- Message rate metrics
- System uptime
- Connected devices table

**MQTT Config Tab:**
- Broker information (host, port, status)
- Security settings (username, TLS, protocol)
- MQTT statistics (topics, clients, message rate)

**MQTT Logs Tab:**
- Real-time MQTT broker logs
- Color-coded log levels
- Filtered for MQTT-specific events
- Auto-refresh every 3 seconds

**Configuration Tab:**
- Gateway information (ID, version, uptime)
- Database status
- System resources (memory, CPU, disk)

#### 3. **API Documentation** (`/api-docs`)
- Swagger-like interactive interface
- Module-based organization
- Try-it-out functionality
- **File upload support** (drag & drop or click)
- Search and filter endpoints
- Copy endpoint URL to clipboard

#### 4. **System Logs** (`/logs`)
- Real-time application logs
- Color-coded by severity
- Log level filtering
- Download as text file
- Clear logs functionality

### API Endpoints

#### Authentication
```
POST /api/users/login/web
  Body: {email_address, password}
  Response: {access_token, user_id, email}
```

#### Devices
```
GET    /api/device                      # List all devices
POST   /api/device                      # Create device
GET    /api/device/<id>                 # Get device details
PUT    /api/device/<id>                 # Update device
DELETE /api/device/<id>                 # Delete device
```

#### Firmware
```
GET    /api/firmware                    # List firmware
POST   /api/firmware                    # Upload firmware
PUT    /api/firmware/<id>               # Update firmware
DELETE /api/firmware/<id>               # Delete firmware
```

#### MQTT
```
GET  /api/mqtt/broker-logs              # Get broker statistics
POST /api/mqtt/auth                     # Create MQTT auth
```

#### Gateway
```
GET  /api/gateway/data                  # Dashboard data
GET  /api/gateway/config                # Gateway config
POST /api/gateway/config                # Update config
```

---

## 🗄️ Database Schema

### MongoDB Collections

#### Users Collection
```json
{
  "_id": ObjectId,
  "email_address": "user@example.com",
  "password": "hashed_password",
  "username": "username",
  "role": "admin|user|viewer",
  "status": "active|inactive",
  "created_at": ISODate,
  "last_login": ISODate
}
```

#### Devices Collection
```json
{
  "_id": ObjectId,
  "device_id": "DV-001",
  "device_type_id": ObjectId,
  "client_id": "unique_client_id",
  "name": "Device Name",
  "status": "online|offline",
  "location": "Building A, Room 101",
  "firmware_version": "1.0.0",
  "connection": {
    "status": "online|offline",
    "last_update": "2026-05-07 20:11:46",
    "signal_strength": -67
  },
  "created_at": ISODate,
  "updated_at": ISODate
}
```

#### Device Types Collection
```json
{
  "_id": ObjectId,
  "name": "ESP32 Sensor",
  "description": "Temperature & Humidity Sensor",
  "manufacturer": "Espressif",
  "model": "ESP32-WROVER",
  "specifications": {
    "cpu": "Xtensa 240MHz",
    "ram": "520KB",
    "storage": "4MB"
  }
}
```

#### Firmware Collection
```json
{
  "_id": ObjectId,
  "name": "Firmware v1.0.0",
  "version": "1.0.0",
  "device_type_id": ObjectId,
  "file_url": "/firmware_files/12345.bin",
  "file_size": 524288,
  "checksum": "sha256_hash",
  "release_notes": "Initial release",
  "created_at": ISODate
}
```

#### Tokens Collection
```json
{
  "_id": ObjectId,
  "user_id": ObjectId,
  "token": "unique_token_string",
  "type": "web|mobile|device",
  "expires_at": ISODate,
  "created_at": ISODate
}
```

---

## 📡 MQTT Integration

### MQTT Topics Structure

```
ZV/DEVICES/
├── <device_id>/
│   ├── status/         # Device status updates
│   ├── usage/          # Device resource usage
│   └── command/        # Commands to device
```

### $SYS Topics (Broker Stats)
```
$SYS/broker/
├── version             # Broker version
├── uptime              # Uptime in seconds
├── clients/total       # Total clients ever connected
├── clients/connected   # Currently connected clients
├── messages/stored     # Messages in storage
├── messages/received/total
├── messages/sent/total
├── publish/messages/received
└── load/messages/received/1min
```

### MQTT Client Service

**File:** `esp32OTA/Services/mqtt_client.py`

```python
# Subscribe to broker stats
client.subscribe("$SYS/broker/#", qos=1)

# Subscribe to device status
client.subscribe("ZV/DEVICES/+/status/#", qos=1)

# Subscribe to device usage
client.subscribe("ZV/DEVICES/+/usage/#", qos=1)
```

### MQTT Authentication

**Mosquitto ACL File:** `mosquitto_acl.conf`

```conf
# Admin user - full access
user admin_mqtt
topic write $SYS/#
topic readwrite #

# Device user - limited access
user device_user
topic write ZV/DEVICES/+/status
topic write ZV/DEVICES/+/usage
topic read ZV/DEVICES/+/command

# Read-only user
user viewer
topic read #
```

---

## 🚀 Deployment

### Option 1: Systemd Service (Linux)

**File:** `esp32-ota.service`

```bash
# Copy service file
sudo cp esp32-ota.service /etc/systemd/system/

# Enable and start
sudo systemctl enable esp32-ota
sudo systemctl start esp32-ota

# Check status
sudo systemctl status esp32-ota

# View logs
sudo journalctl -u esp32-ota -f
```

### Option 2: Docker

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["gunicorn", "--config", "gunicorn.conf.py", "wsgi:app"]
```

```bash
# Build
docker build -t zvolta:latest .

# Run
docker run -p 5000:5000 \
  -e MONGODB_URI="mongodb://mongo:27017/zvolta" \
  -e MQTT_HOST="mqtt" \
  zvolta:latest
```

### Option 3: Docker Compose

```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "5000:5000"
    environment:
      MONGODB_URI: mongodb://mongo:27017/zvolta
      MQTT_HOST: mqtt
    depends_on:
      - mongo
      - mqtt

  mongo:
    image: mongo:5.0
    volumes:
      - mongo_data:/data/db

  mqtt:
    image: eclipse-mosquitto:latest
    ports:
      - "1883:1883"
      - "9001:9001"
    volumes:
      - ./mosquitto.conf:/mosquitto/config/mosquitto.conf
      - ./mosquitto_acl.conf:/mosquitto/config/acl.conf
      - mqtt_data:/mosquitto/data

volumes:
  mongo_data:
  mqtt_data:
```

---

## 🔍 Troubleshooting

### Issue 1: MQTT Connection Failed
```
Error: [MQTT] Connection failed with code 1
```

**Solutions:**
1. Check Mosquitto is running: `sudo systemctl status mosquitto`
2. Verify host and port in config
3. Check firewall rules: `sudo ufw allow 1883`
4. Verify credentials in mosquitto_acl.conf

### Issue 2: MongoDB Connection Error
```
Error: Failed to connect to MongoDB
```

**Solutions:**
1. Start MongoDB: `sudo systemctl start mongod`
2. Check connection string in config
3. Verify authentication credentials
4. Check network connectivity: `nc -zv localhost 27017`

### Issue 3: File Upload Failing
```
Error: File upload size exceeds limit
```

**Solutions:**
1. Check MAX_UPLOAD_SIZE in config
2. Verify /firmware_files directory permissions
3. Check disk space: `df -h`

### Issue 4: Authentication Token Expired
```
Error: 401 Unauthorized - Token expired
```

**Solutions:**
1. Clear browser cache and localStorage
2. Login again to get new token
3. Check token expiry in database
4. Sync server time: `sudo ntpdate ntp.ubuntu.com`

### Issue 5: Logs Not Appearing
```
No logs visible in dashboard
```

**Solutions:**
1. Check application logs are being written
2. Verify logging level in config
3. Check /var/log/zvolta/ permissions
4. Restart application: `sudo systemctl restart esp32-ota`

---

## 📊 Monitoring

### New Relic Integration

**File:** `newrelic.ini`

```ini
[newrelic]
license_key = YOUR_LICENSE_KEY
app_name = ZVOLTA Gateway
enable_harvest_limits = true
```

### Health Check Endpoint

```bash
curl http://localhost:5000/scheduler/status
```

Response:
```json
{
  "scheduler": "running",
  "uptime": "2 days 4 hours 23 minutes",
  "jobs": 5,
  "next_run": "2026-05-07 21:00:00"
}
```

---

## 🔐 Security Best Practices

1. **Passwords:**
   - Always use strong passwords (min 12 characters)
   - Never commit credentials to git
   - Use environment variables for secrets

2. **MQTT:**
   - Enable authentication and ACL
   - Use TLS for production
   - Rotate credentials regularly

3. **API:**
   - Always use HTTPS in production
   - Implement rate limiting
   - Validate all inputs
   - Use CORS carefully

4. **Database:**
   - Enable MongoDB authentication
   - Use network segmentation
   - Regular backups
   - Encrypt data at rest

---

## 📚 API Documentation

Full interactive API documentation available at:
```
http://localhost:5000/api-docs
```

Features:
- ✅ All endpoints listed with methods
- ✅ Try-it-out functionality
- ✅ Authentication headers auto-populated
- ✅ File upload support
- ✅ Real-time response display
- ✅ Search and filter

---

## 🛠️ Development

### Running in Development Mode
```bash
export FLASK_ENV=development
export FLASK_DEBUG=1
python app.py
```

### Running Tests
```bash
pytest tests/
```

### Code Style
```bash
# Format code
black esp32OTA/

# Lint code
pylint esp32OTA/
```

---

## 📝 License

This project is licensed under the MIT License - see LICENSE file for details.

---

## 👥 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

---

## 📞 Support

For issues, questions, or suggestions:
- Create an issue on GitHub
- Email: support@zvolta.com
- Documentation: https://docs.zvolta.com

---

## 🙏 Acknowledgments

- Flask team for the excellent web framework
- MongoDB for the database
- Eclipse Mosquitto for MQTT
- All contributors and users

---

**Last Updated:** May 7, 2026  
**Version:** 1.0.0  
**Status:** Production Ready ✅

---

For more information, visit: https://github.com/zvolta/zvolta-gateway