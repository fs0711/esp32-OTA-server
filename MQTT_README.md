# MQTT Communication Protocol - ZVOLTA

This document outlines the MQTT communication structure used in the ESP32 OTA project, including topics, payloads, and the logic applied by the server.

## 1. Top-Level Topic Prefix
All topics are prefixed with `ZV/DEVICES/` to distinguish project traffic.

---

## 2. Server Subscriptions (Listening)

The server listens for status and telemetry data from devices on the following topics:

### A. Device Status
- **Topic**: `ZV/DEVICES/+/status/#`
- **Pattern**: `ZV/DEVICES/{device_id}/status`
- **Incoming Payload (Device -> Server)**: 
  ```json
  {
    "t": 123456789, 
    "s": [
      {
        "id": 1, 
        "st": 1, 
        "sg": "w", 
        "e": ["E2"]
      }
    ], 
    "e": []
  }
  ```
- **Mapped Payload (Server -> API)**:
  ```json
  {
    "c_s_id": 123,
    "s": [
      {
        "id": 1,
        "status": 1,
        "signal_type": "wifi",
        "e": ["E2"]
      }
    ],
    "e": []
  }
  ```
- **Logic**: 
  - **Deduplication**: Validates uniqueness using the timestamp (`t`).
  - **Client ID Lookup**: Finds `client_id` (c_s_id) from the database using `device_id`.
  - **Mapping**: Converts `st` to `status` and `sg` to `signal_type` (`w` -> `wifi`, `g` -> `gsm`).
  - **Logging**: Always logs to terminal; saves to database activity log **only if error codes (`e`) are present**.
  - **API**: Forwards to `{ORKOFLEET_BASE_URL}/api/v2/power-sockets/status`.
  - **Cache**: Updates `GatewayService` last-seen status.

### B. Device Usage
- **Topic**: `ZV/DEVICES/+/usage/#`
- **Pattern**: `ZV/DEVICES/{device_id}/usage`
- **Incoming Payload (Device -> Server)**:
  ```json
  {
    "t": 123456789,
    "d": {
      "s": 1,
      "se": "sess_123",
      "co": 1500,
      "cu": 5.2,
      "v": 230,
      "d": 3600,
      "is": true
    }
  }
  ```
- **Mapped Payload (Server -> API)**:
  ```json
  {
    "socket_id": 1,
    "session_id": "sess_123",
    "consumption": 1500,
    "current": 5.2,
    "voltage": 230,
    "duration": 3600,
    "is_completed": true
  }
  ```
- **Logic**:
  - **Deduplication**: Prevents processing duplicate timestamps.
  - **Field Mapping**: 
    - `s` -> `socket_id`
    - `se` -> `session_id`
    - `co` -> `consumption`
    - `cu` -> `current`
    - `v` -> `voltage`
    - `d` -> `duration`
    - `is` -> `is_completed`
  - **API**: Forwards to `{ORKOFLEET_BASE_URL}/api/v2/charge-sessions/add-usage-data`.

### C. Broker Stats
- **Topic**: `$SYS/broker/#`
- **Logic**: Monitors internal broker health and connection statistics.

---

## 3. Server Publications (Sending)

The server sends commands and update notifications to devices on these topics:

### A. Configuration Update Notification
- **Topic**: `ZV/DEVICES/{device_id}/config`
- **Payload**: `{"s": "update_required", "t": 1778095523}`
- **Logic**: 
  - Triggered automatically when a device's configuration is modified via the `DeviceController`.
  - Notifies the device that it needs to fetch new settings.
  - Timestamp (`t`) is in Epoch format.

### B. Firmware Update Command
- **Topic**: `ZV/DEVICES/{device_id}/firmware`
- **Payload**: `{"t": 1778095523, "f_f": "FIRMWARE_OBJECT_ID", "f_v": "1", "h_v": "1", "n_v": "2", "u_p": "immediate"}`
- **Logic**:
  - Sent by the `FirmwareController` when a new OTA update is initiated.
  - Instructs the device on which file to download (using its ID) and whether to apply it immediately.

---

## 4. Topic Overview Table

| Topic Prefix | Direction | Purpose |
| :--- | :--- | :--- |
| `ZV/DEVICES/{id}/status` | Device -> Server | Heartbeat, signal strength, socket states |
| `ZV/DEVICES/{id}/usage` | Device -> Server | Energy consumption and usage logs |
| `ZV/DEVICES/{id}/config` | Server -> Device | Signal that DB config data has changed |
| `ZV/DEVICES/{id}/firmware` | Server -> Device | OTA firmware upgrade instructions |

---

## 5. Security & Consistency
- **QoS**: Most messages use **QoS 1** (At Least Once) to ensure critical commands like firmware updates reach the device.
- **De-duplication**: The server implements a timestamp-based cache to ignore repeated messages from the device, preventing excessive API calls.

status
  {
    "t": 123456789, 
    "s": [
      {
        "id": 1, 
        "st": 1, 
        "sg": "w", 
        "e": ["E2"]
      }
    ], 
    "e": []
  }

usage
    {
    "t": 123456789,
    "d": {
      "s": 1,
      "se": "sess_123",
      "co": 0,
      "cu": 5.2,
      "v": 230,
      "d": 3600,
      "is": 1
    }
  }