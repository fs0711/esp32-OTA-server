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


def generate_hmac_password(device_id, access_token):
    """
    Generate HMAC-SHA256 password for MQTT authentication
    
    Args:
        device_id (str): Device ID (MQTT username)
        access_token (str): Device access token (HMAC secret key)
    
    Returns:
        str: HMAC-SHA256 hexdigest
    """
    signature = hmac.new(
        access_token.encode('utf-8'),
        device_id.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return signature


def main():
    # Check if called with positional arguments
    if len(sys.argv) == 3 and not sys.argv[1].startswith('--'):
        device_id = sys.argv[1]
        access_token = sys.argv[2]
    else:
        # Use argparse for named arguments
        parser = argparse.ArgumentParser(
            description='Generate HMAC-SHA256 password for MQTT authentication'
        )
        parser.add_argument(
            '--device-id',
            required=True,
            help='Device ID (MQTT username)'
        )
        parser.add_argument(
            '--access-token',
            required=True,
            help='Device access token (HMAC secret key)'
        )
        parser.add_argument(
            '--format',
            choices=['plain', 'json', 'env'],
            default='plain',
            help='Output format (default: plain)'
        )
        
        args = parser.parse_args()
        device_id = args.device_id
        access_token = args.access_token
        output_format = args.format if hasattr(args, 'format') else 'plain'
    
    # Generate HMAC password
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
