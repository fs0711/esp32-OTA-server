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
        tuple: (password, rounded_timestamp, creation_timestamp)
    """
    # Capture the exact time of creation
    creation_timestamp = int(time.time())
    
    # Round down current time to the nearest 5 minutes (300 seconds)
    rounded_timestamp = str(creation_timestamp - (creation_timestamp % 300))
    
    # Use device_id AND the rounded timestamp in the HMAC message
    message = f"{device_id}{rounded_timestamp}"
    
    signature = hmac.new(
        access_token.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    # Generate a simple reversible "hash" (Base64 encoded) rounded timestamp
    encoded_timestamp = base64.b64encode(rounded_timestamp.encode()).decode().rstrip('=')
    
    # Append the reversible timestamp to the HMAC signature (No separator)
    password = f"{signature}{encoded_timestamp}"
    return password, rounded_timestamp, str(creation_timestamp)


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
    
    # Generate HMAC password using id and token, capturing the timestamps
    password, timestamp_used, creation_time = generate_hmac_password(device_id, access_token)
    
    # Output based on format
    if 'output_format' in locals() and output_format == 'json':
        import json
        print(json.dumps({
            'device_id': device_id,
            'username': device_id,
            'password': password,
            'timestamp_used': timestamp_used,
            'creation_time': creation_time,
            'algorithm': 'HMAC-SHA256'
        }, indent=2))
    elif 'output_format' in locals() and output_format == 'env':
        print(f"MQTT_USERNAME={device_id}")
        print(f"MQTT_PASSWORD={password}")
        print(f"MQTT_TIMESTAMP={timestamp_used}")
        print(f"MQTT_CREATED_AT={creation_time}")
    else:
        print(f"\n{'='*70}")
        print("MQTT Authentication Credentials")
        print(f"{'='*70}")
        print(f"Device ID:      {device_id}")
        print(f"Access Token:   {access_token}")
        print(f"Created At:     {creation_time}")
        print(f"Timestamp Used: {timestamp_used}")
        print(f"{'='*70}")
        print(f"Username:       {device_id}")
        print(f"Password:       {password}")
        print(f"{'='*70}\n")


if __name__ == '__main__':
    main()
