#!/usr/bin/env python3
"""
MQTT Authentication Test Script
Tests HMAC-based authentication with the ESP32 OTA Backend

Usage:
    python test_mqtt_auth.py --device-id DV-001 --access-token <token>
"""

import argparse
import hmac
import hashlib
import requests
import json


def generate_hmac_password(device_id, access_token):
    """
    Generate HMAC-SHA256 password for MQTT authentication
    
    Args:
        device_id (str): Device ID (username)
        access_token (str): Device access token (HMAC secret key)
    
    Returns:
        str: HMAC-SHA256 hexdigest to use as password
    """
    signature = hmac.new(
        access_token.encode('utf-8'),
        device_id.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return signature


def test_authentication(base_url, device_id, password):
    """
    Test MQTT authentication endpoint
    
    Args:
        base_url (str): Backend base URL (e.g., http://localhost:5000)
        device_id (str): Device ID
        password (str): HMAC password
    
    Returns:
        dict: Response from authentication endpoint
    """
    url = f"{base_url}/api/mqtt/auth"
    data = {
        'username': device_id,
        'password': password
    }
    
    print(f"\n{'='*60}")
    print("Testing Authentication Endpoint")
    print(f"{'='*60}")
    print(f"URL: {url}")
    print(f"Username: {device_id}")
    print(f"Password (HMAC): {password[:20]}...{password[-20:]}")
    print(f"{'='*60}\n")
    
    try:
        response = requests.post(url, data=data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}\n")
        return response.json()
    except Exception as e:
        print(f"Error: {e}\n")
        return None


def test_superuser(base_url, device_id):
    """
    Test MQTT superuser endpoint
    
    Args:
        base_url (str): Backend base URL
        device_id (str): Device ID
    
    Returns:
        dict: Response from superuser endpoint
    """
    url = f"{base_url}/api/mqtt/superuser"
    data = {
        'username': device_id
    }
    
    print(f"\n{'='*60}")
    print("Testing Superuser Endpoint")
    print(f"{'='*60}")
    print(f"URL: {url}")
    print(f"Username: {device_id}")
    print(f"{'='*60}\n")
    
    try:
        response = requests.post(url, data=data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}\n")
        return response.json()
    except Exception as e:
        print(f"Error: {e}\n")
        return None


def test_acl(base_url, device_id, topic, access_type='2'):
    """
    Test MQTT ACL endpoint
    
    Args:
        base_url (str): Backend base URL
        device_id (str): Device ID
        topic (str): MQTT topic to test
        access_type (str): '1' for subscribe, '2' for publish
    
    Returns:
        dict: Response from ACL endpoint
    """
    url = f"{base_url}/api/mqtt/acl"
    data = {
        'username': device_id,
        'topic': topic,
        'acc': access_type
    }
    
    access_name = "Publish" if access_type == '2' else "Subscribe"
    
    print(f"\n{'='*60}")
    print(f"Testing ACL Endpoint ({access_name})")
    print(f"{'='*60}")
    print(f"URL: {url}")
    print(f"Username: {device_id}")
    print(f"Topic: {topic}")
    print(f"Access Type: {access_name} ({access_type})")
    print(f"{'='*60}\n")
    
    try:
        response = requests.post(url, data=data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}\n")
        return response.json()
    except Exception as e:
        print(f"Error: {e}\n")
        return None


def print_mqtt_credentials(device_id, password):
    """
    Print MQTT connection credentials
    """
    print(f"\n{'='*60}")
    print("MQTT Connection Credentials")
    print(f"{'='*60}")
    print(f"Username: {device_id}")
    print(f"Password: {password}")
    print(f"\nUse with mosquitto_pub:")
    print(f'mosquitto_pub -h localhost -u "{device_id}" -P "{password}" \\')
    print(f'  -t "devices/{device_id}/test" -m "Hello World"')
    print(f"\nUse with mosquitto_sub:")
    print(f'mosquitto_sub -h localhost -u "{device_id}" -P "{password}" \\')
    print(f'  -t "devices/{device_id}/#"')
    print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(
        description='Test MQTT authentication endpoints'
    )
    parser.add_argument(
        '--device-id',
        required=True,
        help='Device ID (e.g., DV-001)'
    )
    parser.add_argument(
        '--access-token',
        required=True,
        help='Device access token from database'
    )
    parser.add_argument(
        '--base-url',
        default='http://localhost:5000',
        help='Backend base URL (default: http://localhost:5000)'
    )
    parser.add_argument(
        '--skip-auth',
        action='store_true',
        help='Skip authentication test'
    )
    parser.add_argument(
        '--skip-superuser',
        action='store_true',
        help='Skip superuser test'
    )
    parser.add_argument(
        '--skip-acl',
        action='store_true',
        help='Skip ACL test'
    )
    parser.add_argument(
        '--topic',
        default=None,
        help='Custom topic for ACL test (default: devices/<device-id>/test)'
    )
    
    args = parser.parse_args()
    
    # Generate HMAC password
    password = generate_hmac_password(args.device_id, args.access_token)
    
    # Print credentials
    print_mqtt_credentials(args.device_id, password)
    
    # Run tests
    if not args.skip_auth:
        test_authentication(args.base_url, args.device_id, password)
    
    if not args.skip_superuser:
        test_superuser(args.base_url, args.device_id)
    
    if not args.skip_acl:
        topic = args.topic or f"devices/{args.device_id}/test"
        test_acl(args.base_url, args.device_id, topic, access_type='2')
        test_acl(args.base_url, args.device_id, topic, access_type='1')
        
        # Test unauthorized topic
        unauthorized_topic = "devices/OTHER-DEVICE/test"
        print("Testing unauthorized topic access:")
        test_acl(args.base_url, args.device_id, unauthorized_topic, access_type='2')
    
    print("\n✅ All tests completed!\n")


if __name__ == '__main__':
    main()
