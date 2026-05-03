#!/usr/bin/env python3
"""
MQTT HMAC Password Generator
Generates HMAC-SHA256 password for MQTT authentication

Usage:
    python generate_mqtt_password.py DV-001 <access-token>
    python generate_mqtt_password.py --device-id DV-001 --access-token <token>
"""

import sys
import argparse
import hmac
import hashlib
import time
import base64


def generate_hmac_password(device_id, access_token):
    """
    Generate HMAC-SHA256 password for MQTT authentication
    
    Args:
        device_id (str): Device ID (MQTT username)
        access_token (str): Device access token (HMAC secret key)
    
    Returns:
        str: HMAC-SHA256 hexdigest
    """
    # Use device_id as the message
    message = device_id
    
    signature = hmac.new(
        access_token.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    # Generate a simple reversible "hash" (Base64 encoded) timestamp
    timestamp = str(int(time.time()))
    encoded_timestamp = base64.b64encode(timestamp.encode()).decode().rstrip('=')
    
    # Append the reversible timestamp to the HMAC signature
    return f"{signature}:{encoded_timestamp}"


def main():
    # Fix: Remove broken lines and add interactive prompts
    print("\n--- MQTT Password Generator ---")
    device_input = input("Enter Device ID or Number (e.g., 1 or DV-1): ").strip()
    
    # Ensure format is always DV-X
    if device_input.isdigit():
        device_id = f"DV-{device_input}"
    elif device_input.upper().startswith("DV-"):
        device_id = f"DV-{device_input.upper().replace('DV-', '')}"
    else:
        device_id = device_input

    access_token = input("Enter Access Token: ").strip()
    output_format = 'plain'

    if not device_id or not access_token:
        print("Error: Both Device ID and Access Token are required.")
        return
    
    # Generate HMAC password using id and token
    password = generate_hmac_password(device_id, access_token)
    
    # Output based on format
    if 'output_format' in locals() and output_format == 'json':
        import json
        print(json.dumps({
            'device_id': device_id,
            'username': device_id,
            'password': password,
            'algorithm': 'HMAC-SHA256'
        }, indent=2))
    elif 'output_format' in locals() and output_format == 'env':
        print(f"MQTT_USERNAME={device_id}")
        print(f"MQTT_PASSWORD={password}")
    else:
        print(f"\n{'='*70}")
        print("MQTT Authentication Credentials")
        print(f"{'='*70}")
        print(f"Device ID:      {device_id}")
        print(f"Access Token:   {access_token[:10]}...{access_token[-10:]}")
        print(f"{'='*70}")
        print(f"Username:       {device_id}")
        print(f"Password:       {password}")
        print(f"{'='*70}")
        print("\nMosquitto Publish Example:")
        print(f'mosquitto_pub -h localhost -u "{device_id}" -P "{password}" \\')
        print(f'  -t "devices/{device_id}/telemetry" -m "{{\'temp\':25.5}}"')
        print("\nMosquitto Subscribe Example:")
        print(f'mosquitto_sub -h localhost -u "{device_id}" -P "{password}" \\')
        print(f'  -t "devices/{device_id}/#"')
        print(f"{'='*70}\n")


if __name__ == '__main__':
    main()
