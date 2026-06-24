"""
One-time migration script.

For every Device:
  - Clear new_fw_version (set to "")
  - If variables contains a 'fw_version' key:
      - Copy its value to the top-level fw_version field
      - Remove 'fw_version' from variables

Run from the project root:
    python migrate_fw_version.py
"""

from esp32OTA import app
from esp32OTA.DeviceManagement.models.Device import Device

updated = 0
skipped = 0

with app.app_context():
    for device in Device.objects.all():
        update_kwargs = {"set__new_fw_version": ""}

        variables = dict(device.variables or {})
        if "fw_version" in variables:
            fw_val = variables.pop("fw_version")
            update_kwargs["set__fw_version"] = str(fw_val)
            update_kwargs["set__variables"] = variables

        Device.objects(id=device.id).update_one(**update_kwargs)

        had_fw = "set__fw_version" in update_kwargs
        print(
            f"[{'UPDATED' if had_fw else 'CLEARED'}] {device.device_id}"
            + (f" -> fw_version={update_kwargs['set__fw_version']}" if had_fw else "")
        )
        updated += 1

print(f"\nDone. {updated} device(s) processed.")
