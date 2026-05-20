# MQTT Communication Protocol — ZVOLTA Gateway

**Version:** 2.0  
**Broker:** Mosquitto  
**Default Host:** `127.0.0.1:1884`  
**Topic Namespace:** `ZV/DEVICES/`

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Connection & Session Management](#2-connection--session-management)
3. [Server Subscriptions (Inbound Topics)](#3-server-subscriptions-inbound-topics)
   - [Device Status](#31-device-status)
   - [Device Usage](#32-device-usage)
   - [Configuration Request — command](#33-configuration-request--command)
   - [Configuration Request — send_config flag](#34-configuration-request--send_config-flag)
   - [Configuration Request — configuration topic](#35-configuration-request--configuration-topic)
   - [Set Configuration — setconfig](#36-set-configuration--setconfig)
   - [Broker System Stats](#37-broker-system-stats)
4. [Server Publications (Outbound Topics)](#4-server-publications-outbound-topics)
   - [Config Change Notification](#41-config-change-notification)
   - [Full Configuration Push](#42-full-configuration-push)
   - [Firmware OTA Command](#43-firmware-ota-command)
   - [Ping / Socket State Push](#44-ping--socket-state-push)
5. [Complete Topic Reference Table](#5-complete-topic-reference-table)
6. [Field Mapping Reference](#6-field-mapping-reference)
7. [Processing Pipeline](#7-processing-pipeline)
8. [Error Handling & Deduplication](#8-error-handling--deduplication)
9. [QoS & Reliability](#9-qos--reliability)
10. [Downstream API Integration](#10-downstream-api-integration)

---

## 1. Architecture Overview

```
┌────────────────────────────────────────────────────────────────────────┐
│                          ESP32 Devices (Field)                         │
│  Publishes: status, usage, command, send_config, configuration,        │
│             setconfig                                                   │
│  Subscribes: config, configupdate, firmware, ping                      │
└────────────────────────┬───────────────────────────────────────────────┘
                         │  MQTT (QoS 1)
                         ▼
               ┌─────────────────────┐
               │   Mosquitto Broker  │
               │   127.0.0.1:1884    │
               └──────────┬──────────┘
                          │
                          ▼
               ┌─────────────────────┐
               │  MQTTClientService  │  ← Python / Paho singleton
               │  (mqtt_client.py)   │
               └──────────┬──────────┘
                 ┌─────────┼──────────────┐
                 ▼         ▼              ▼
          MongoDB DB   OrkoFleet API   Device DB
          (Device,     /power-sockets  (GatewayService
           Firmware)   /charge-sessions last_updated)
```

The server runs a **singleton** `MQTTClientService` that:
- Connects to Mosquitto on startup and maintains the connection with automatic reconnection.
- Routes each incoming topic to a dedicated handler method.
- Translates compact device payloads to full API payloads before forwarding upstream.
- Publishes commands back to devices in response to API calls or internal triggers.

---

## 2. Connection & Session Management

| Parameter | Value |
| :--- | :--- |
| Keep-alive | 60 seconds |
| Reconnect delay | 5 seconds (automatic, recursive timer) |
| Loop mode | `loop_start()` (background thread) |
| Callback API | Paho `VERSION2` |

**On connect** the server immediately subscribes to all required topics (see §3).  
**On disconnect** `connected = False` is set and a 5-second reconnect timer fires. If the reconnect also fails the timer reschedules itself indefinitely.

---

## 3. Server Subscriptions (Inbound Topics)

The server subscribes to the following topics immediately after every successful broker connection.

---

### 3.1 Device Status

| | |
| :--- | :--- |
| **Subscribed topic** | `ZV/DEVICES/+/status/#` |
| **Effective pattern** | `ZV/DEVICES/{device_id}/status` |
| **Direction** | Device → Server |
| **QoS** | 1 |
| **Handler** | `handle_device_status()` |

#### Device Payload (compact)

```json
{
  "t": 1716300000,
  "s": [
    {
      "id": 1,
      "st": 1,
      "sg": "w",
      "e": ["E2"]
    },
    {
      "id": 2,
      "st": 0,
      "sg": "g",
      "e": []
    }
  ],
  "e": []
}
```

| Field | Type | Description |
| :--- | :--- | :--- |
| `t` | integer | Unix epoch timestamp. Used for deduplication. |
| `s` | array | Per-socket status objects. |
| `s[].id` | integer | Socket identifier. |
| `s[].st` | integer | Socket status (`0` = off, `1` = on). |
| `s[].sg` | string | Signal type: `w` = WiFi, `g` = GSM. |
| `s[].e` | array | Error codes for this socket (empty if none). |
| `e` | array | Device-level error codes (empty if none). |

#### Forwarded API Payload (expanded)

```json
{
  "c_s_id": 42,
  "s": [
    {
      "id": 1,
      "status": 1,
      "signal_type": "wifi",
      "e": ["E2"]
    },
    {
      "id": 2,
      "status": 0,
      "signal_type": "gsm",
      "e": []
    }
  ],
  "e": []
}
```

**API endpoint:** `POST {ORKOFLEET_BASE_URL}/api/v2/power-sockets/status`

#### Processing steps

1. **Deduplication** — compares incoming `t` against `last_timestamps[device_id]`. Silently drops the message if equal.
2. **Device lookup** — queries MongoDB `Device` collection by `device_id` (with string-comparison fallback).
3. **Client ID resolution** — reads `device.client_id` (OrkoFleet's `c_s_id`). Stops processing if not found.
4. **Field mapping** — `st` → `status`; `sg` → `signal_type` (`w` → `"wifi"`, `g` → `"gsm"`).
5. **Error-conditional DB logging** — saves activity log to `GatewayLogging` **only** when any `s[].e` or root `e` contains values.
6. **API forward** — HTTP POST to OrkoFleet with 5-second timeout.
7. **Last-updated cache** — on HTTP 200, calls `GatewayService.update_device_last_updated()` to persist the timestamp.

---

### 3.2 Device Usage

| | |
| :--- | :--- |
| **Subscribed topic** | `ZV/DEVICES/+/usage/#` |
| **Effective pattern** | `ZV/DEVICES/{device_id}/usage` |
| **Direction** | Device → Server |
| **QoS** | 1 |
| **Handler** | `handle_device_usage()` |

#### Device Payload (compact)

```json
{
  "t": 1716300060,
  "d": {
    "s": 1,
    "se": "sess_abc123",
    "co": 1500,
    "cu": 5.2,
    "v": 230,
    "d": 3600,
    "is": 1
  }
}
```

| Field | Type | Description |
| :--- | :--- | :--- |
| `t` | integer | Unix epoch timestamp. Used for deduplication. |
| `d` | object | Usage data object. |
| `d.s` | integer | Socket identifier. |
| `d.se` | string | Charge session identifier. |
| `d.co` | number | Energy consumption (Wh). |
| `d.cu` | number | Current (A). |
| `d.v` | number | Voltage (V). |
| `d.d` | integer | Session duration (seconds). |
| `d.is` | integer/bool | `1` / `true` = session completed. |

#### Forwarded API Payload (expanded)

```json
{
  "socket_id": 1,
  "session_id": "sess_abc123",
  "consumption": 1500,
  "current": 5.2,
  "voltage": 230,
  "duration": 3600,
  "is_completed": 1
}
```

**API endpoint:** `POST {ORKOFLEET_BASE_URL}/api/v2/charge-sessions/add-usage-data`

#### Processing steps

1. **Deduplication** — compares `t` against `last_usage_timestamps[device_id]`.
2. **Field mapping** — `s`→`socket_id`, `se`→`session_id`, `co`→`consumption`, `cu`→`current`, `v`→`voltage`, `d`→`duration`, `is`→`is_completed`.
3. **API forward** — HTTP POST to OrkoFleet with 5-second timeout.

---

### 3.3 Configuration Request — command

| | |
| :--- | :--- |
| **Subscribed topic** | `ZV/DEVICES/+/command` |
| **Direction** | Device → Server |
| **QoS** | 1 |
| **Handler** | `handle_config_request()` |
| **Rate limit** | Once per second per device |

A device publishes any payload to this topic when it wants the server to push its current configuration. The server enforces a 1-second cooldown per device using `last_config_request_time` to prevent request storms.

**Example device publish:**
```
Topic:   ZV/DEVICES/DV-5/command
Payload: (any, e.g. "1" or empty)
```

On receipt the server calls `handle_config_request(device_id)` which publishes back to `ZV/DEVICES/{device_id}/configupdate` (see §4.2).

---

### 3.4 Configuration Request — send_config flag

| | |
| :--- | :--- |
| **Subscribed topic** | `ZV/DEVICES/+/send_config` |
| **Direction** | Device → Server |
| **QoS** | 1 |
| **Handler** | `handle_config_request()` |

A device can embed a `send_config` key in any JSON payload on **any** `ZV/DEVICES/+/...` topic. When the server detects `"send_config": 1` in the decoded JSON body it immediately calls `handle_config_request(device_id)`.

**Example device publish:**
```json
{
  "send_config": 1
}
```

---

### 3.5 Configuration Request — configuration topic

| | |
| :--- | :--- |
| **Subscribed topic** | `ZV/DEVICES/+/configuration` |
| **Direction** | Device → Server |
| **QoS** | 1 |
| **Handler** | `handle_config_request()` |

Explicit topic-based config request. Any message on this topic (regardless of payload) triggers a config push to the device.

**Example device publish:**
```
Topic:   ZV/DEVICES/DV-5/configuration
Payload: (any)
```

---

### 3.6 Set Configuration — setconfig

| | |
| :--- | :--- |
| **Subscribed topic** | `ZV/DEVICES/+/setconfig` |
| **Direction** | Device → Server |
| **QoS** | 1 |
| **Handler** | `handle_setconfig()` |

The device sends hardware version and variable data which is applied directly to the device record in the database.

#### Device Payload

```json
{
  "hw_version": "0.1",
  "variables": {
    "key1": "value1",
    "key2": "value2"
  }
}
```

| Field | Type | Description |
| :--- | :--- | :--- |
| `hw_version` | string | Hardware version string of the device. |
| `variables` | object | Key-value configuration map to persist. |

#### Processing steps

1. JSON decoded from payload.
2. `DeviceController.config_controller(data, method="POST", device_id_str=...)` is invoked inside an app context.
3. Device record in MongoDB is partially updated with the supplied fields.

---

### 3.7 Broker System Stats

| | |
| :--- | :--- |
| **Subscribed topic** | `$SYS/broker/#` |
| **Direction** | Broker → Server (internal) |
| **QoS** | 1 |

Mosquitto publishes internal metrics (active connections, messages per second, uptime, etc.) under the `$SYS` hierarchy. The server stores these in the `broker_stats` dictionary, accessible via `GatewayService.get_broker_stats()`.

---

## 4. Server Publications (Outbound Topics)

---

### 4.1 Config Change Notification

| | |
| :--- | :--- |
| **Published topic** | `ZV/DEVICES/{device_id}/config` |
| **Direction** | Server → Device |
| **QoS** | 1 |
| **Triggered by** | `DeviceController.update_controller()` |

Sent immediately after a device record is updated via the REST API. Signals the device that its configuration has changed and it should request the new config.

#### Payload

```json
{
  "s": "update_required",
  "t": 1716300000
}
```

| Field | Type | Description |
| :--- | :--- | :--- |
| `s` | string | Status signal. Always `"update_required"`. |
| `t` | integer | Unix epoch timestamp of the change. |

---

### 4.2 Full Configuration Push

| | |
| :--- | :--- |
| **Published topic** | `ZV/DEVICES/{device_id}/configupdate` |
| **Direction** | Server → Device |
| **QoS** | 1 |
| **Triggered by** | `handle_config_request()`, `DeviceController.config_controller()` (force update) |

Delivers the complete device configuration including all named variables and the QR code. Published in response to any of the three config request mechanisms (§3.3, §3.4, §3.5) or via a manual force-update API call.

#### Payload

```json
{
  "t": 1716300000,
  "variables": {
    "ssid": "NetworkName",
    "pass": "password123",
    "interval": 30
  },
  "qr_code": "ZV-DV5-SERIAL-XXXX"
}
```

| Field | Type | Description |
| :--- | :--- | :--- |
| `t` | integer | Unix epoch timestamp. |
| `variables` | object | Full device variable map from the database. |
| `qr_code` | string | Device QR code string. |

---

### 4.3 Firmware OTA Command

| | |
| :--- | :--- |
| **Published topic** | `ZV/DEVICES/{device_id}/firmware` |
| **Direction** | Server → Device |
| **QoS** | 1 |
| **Triggered by** | `FirmwareController.assign_controller()` |

Sent to every active device matching a firmware's `device_type` and `hw_version` when a new firmware is assigned. The device uses this payload to initiate an OTA download.

#### Payload

```json
{
  "t": 1716300000,
  "f_f": "64a3e9c2f1b2a30012345678",
  "f_v": "1.0.0",
  "h_v": "0.1",
  "n_v": "1.1.0",
  "u_p": "immediate"
}
```

| Field | Type | Description |
| :--- | :--- | :--- |
| `t` | integer | Unix epoch timestamp. |
| `f_f` | string | MongoDB ObjectId of the firmware file record. |
| `f_v` | string | Current firmware version on the device. |
| `h_v` | string | Hardware version the firmware targets. |
| `n_v` | string | New firmware version being pushed. |
| `u_p` | string | Update path / strategy (e.g. `"immediate"`). |

The device downloads the binary from:
```
GET /firmware/download/{f_f}
```

---

### 4.4 Ping / Socket State Push

| | |
| :--- | :--- |
| **Published topic** | `ZV/DEVICES/{device_id}/ping` |
| **Direction** | Server → Device |
| **QoS** | 1 |
| **Triggered by** | `DeviceController.ping_controller()` via REST API |

Pushes real-time socket state from OrkoFleet down to the physical device. The OrkoFleet platform calls the REST endpoint which translates the full field names to compact keys before publishing.

#### REST API Payload (received from OrkoFleet)

```json
{
  "c_s_id": 42,
  "s": [
    {
      "status": 0,
      "session_id": "sess_abc",
      "credit": 10.5
    }
  ]
}
```

#### MQTT Payload (published to device — compact)

```json
{
  "t": 1716300000,
  "s": [
    {
      "st": 0,
      "sid": "sess_abc",
      "cr": 10.5
    }
  ]
}
```

| REST field | MQTT field | Description |
| :--- | :--- | :--- |
| `status` | `st` | Socket on/off state. |
| `session_id` | `sid` | Active charge session ID. |
| `credit` | `cr` | Remaining credit balance. |

---

## 5. Complete Topic Reference Table

| Topic | Direction | QoS | Purpose | Handler / Trigger |
| :--- | :---: | :---: | :--- | :--- |
| `ZV/DEVICES/{id}/status` | Device → Server | 1 | Socket states, signal, errors | `handle_device_status()` |
| `ZV/DEVICES/{id}/usage` | Device → Server | 1 | Energy consumption data | `handle_device_usage()` |
| `ZV/DEVICES/{id}/command` | Device → Server | 1 | Config pull request | `handle_config_request()` |
| `ZV/DEVICES/{id}/send_config` | Device → Server | 1 | Inline config pull flag | `handle_config_request()` |
| `ZV/DEVICES/{id}/configuration` | Device → Server | 1 | Explicit config pull | `handle_config_request()` |
| `ZV/DEVICES/{id}/setconfig` | Device → Server | 1 | Device writes its own config | `handle_setconfig()` |
| `$SYS/broker/#` | Broker → Server | 1 | Broker health metrics | `broker_stats` dict |
| `ZV/DEVICES/{id}/config` | Server → Device | 1 | Config change signal | `DeviceController.update_controller()` |
| `ZV/DEVICES/{id}/configupdate` | Server → Device | 1 | Full config push | `handle_config_request()` / force update |
| `ZV/DEVICES/{id}/firmware` | Server → Device | 1 | OTA firmware command | `FirmwareController.assign_controller()` |
| `ZV/DEVICES/{id}/ping` | Server → Device | 1 | Socket state from OrkoFleet | `DeviceController.ping_controller()` |

---

## 6. Field Mapping Reference

### Status topic — compact → expanded

| Device field | API field | Notes |
| :--- | :--- | :--- |
| `t` | _(dedup only)_ | Not forwarded to API |
| `s[].id` | `s[].id` | Unchanged |
| `s[].st` | `s[].status` | |
| `s[].sg = "w"` | `s[].signal_type = "wifi"` | WiFi |
| `s[].sg = "g"` | `s[].signal_type = "gsm"` | GSM |
| `s[].e` | `s[].e` | Unchanged |
| `e` | `e` | Root error codes, unchanged |
| _(device lookup)_ | `c_s_id` | Resolved from `Device.client_id` |

### Usage topic — compact → expanded

| Device field | API field |
| :--- | :--- |
| `d.s` | `socket_id` |
| `d.se` | `session_id` |
| `d.co` | `consumption` |
| `d.cu` | `current` |
| `d.v` | `voltage` |
| `d.d` | `duration` |
| `d.is` | `is_completed` |

### Ping topic — expanded → compact

| REST field | MQTT field |
| :--- | :--- |
| `status` | `st` |
| `session_id` | `sid` |
| `credit` | `cr` |

---

## 7. Processing Pipeline

### Inbound status message flow

```
Device publishes to ZV/DEVICES/{id}/status
        │
        ▼
on_message() — topic routing
        │
        ▼
Deduplication check (timestamp cache)
        │ duplicate → DROP (silent)
        │ unique ↓
        ▼
handle_device_status()
        │
        ├─► MongoDB: Device.objects(device_id=...) → resolve client_id
        │
        ├─► Map compact fields to expanded API fields
        │
        ├─► (if errors present) → GatewayLogging DB write
        │
        ├─► HTTP POST → OrkoFleet /api/v2/power-sockets/status
        │
        └─► (if HTTP 200) → GatewayService.update_device_last_updated()
```

### Config request flow

```
Device publishes to .../command  OR  .../configuration  OR  send_config=1
        │
        ▼
handle_config_request(device_id)
        │
        ├─► MongoDB: Device.objects(device_id=...) → load variables + qr_code
        │
        └─► MQTT publish → ZV/DEVICES/{id}/configupdate
              {t, variables, qr_code}
```

### Firmware OTA flow

```
REST API: POST /firmware/assign
        │
        ▼
FirmwareController.assign_controller()
        │
        ├─► MongoDB: find matching devices by device_type + hw_version
        │
        ├─► For each device: Device.update(new_fw_version, fw_file, ...)
        │
        └─► MQTT publish → ZV/DEVICES/{id}/firmware
              {t, f_f, f_v, h_v, n_v, u_p}
```

---

## 8. Error Handling & Deduplication

### Timestamp-based deduplication

Two independent caches prevent redundant processing:

| Cache | Scope | Used by |
| :--- | :--- | :--- |
| `last_timestamps` | Per device | `handle_device_status()` |
| `last_usage_timestamps` | Per device | `handle_device_usage()` |

A message is silently dropped (no log, no DB write, no API call) if its `t` field equals the cached value for that device.

### Command rate limiting

The `last_config_request_time` dict enforces a minimum 1-second gap between config requests from the same device on the `command` topic. Requests arriving faster than 1 second are dropped with a `DEBUG` log entry.

### Device not found

If a device publishes a status or usage message but cannot be resolved in the database, processing stops silently. No API call is made and no error is surfaced to the device.

### API timeout

All HTTP calls to OrkoFleet use a 5-second timeout. Failures are caught and logged at `ERROR` level; they do not cause reconnection or message re-delivery.

### JSON decode failures

If a device sends a non-JSON payload on a topic that expects JSON, the error is caught and logged at `ERROR` level. The message is discarded.

---

## 9. QoS & Reliability

| Level | Applied to | Guarantee |
| :--- | :--- | :--- |
| QoS 1 | All `ZV/DEVICES/` topics (both directions) | At-least-once delivery |
| QoS 1 | `$SYS/broker/#` | At-least-once delivery |

**Why QoS 1 and not QoS 2?** QoS 1 is sufficient because the server implements application-level deduplication via timestamp comparison. Re-delivered messages are detected and discarded without any side effects.

---

## 10. Downstream API Integration

All outbound HTTP calls target `ORKOFLEET_BASE_URL` (configured in `config.py`).

| API Endpoint | Method | Triggered by |
| :--- | :---: | :--- |
| `/api/v2/power-sockets/status` | POST | Every unique status message |
| `/api/v2/charge-sessions/add-usage-data` | POST | Every unique usage message |

Both calls include `Content-Type: application/json` and a 5-second request timeout. Response bodies are logged at `INFO` level for diagnostics but are not persisted to the database unless an error condition is also present in the payload.