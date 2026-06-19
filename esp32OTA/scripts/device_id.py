# One-time script to sync each Device.document_id into variables['device_id']

from esp32OTA import app
from esp32OTA.DeviceManagement.models.Device import Device


def sync_device_id_to_variables():
    """Sync each Device.device_id into Device.variables['device_id']."""
    with app.test_request_context():
        devices = Device.objects.only('device_id', 'variables')
        updated_count = 0
        total_count = 0

        for device in devices:
            total_count += 1
            device_id = str(device.device_id)
            variables = device.variables if isinstance(device.variables, dict) else {}
            if variables.get('device_id') != device_id:
                variables['device_id'] = device_id
                # Use atomic update to avoid validation issues with required fields
                Device.objects(id=device.id).update_one(set__variables=variables)
                updated_count += 1
                print(f"Updated {device_id}")
            else:
                print(f"Already synced {device_id}")

        print(f"Processed {total_count} devices. Updated {updated_count}.")
        return updated_count


def main():
    print("Running one-time device_id -> variables['device_id'] sync...")
    sync_device_id_to_variables()


if __name__ == '__main__':
    main()
