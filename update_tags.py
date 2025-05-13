import csv
import time
from falconpy import Hosts

# API credentials
CLIENT_ID = ""
CLIENT_SECRET = ""

falcon = Hosts(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)

def read_host_data(csv_file):
    try:
        with open(csv_file, mode='r', encoding='utf-8-sig', newline='') as file:
            reader = csv.DictReader(file)
            rows = [row for row in reader if row.get("host")]
            print(f"✅ Successfully read {len(rows)} rows from {csv_file}")
            return rows
    except Exception as e:
        print(f"❌ Error reading CSV: {e}")
        return []

def get_device_id_by_hostname(hostname):
    try:
        # Query for matching device IDs
        query_result = falcon.query_devices_by_filter(
            filter=f"hostname:'{hostname}*'"
        )

        resources = query_result.get("body", {}).get("resources", [])

        if not resources:
            print(f"⚠️ No device found for hostname: {hostname}")
            return None

        # Return first matched device ID
        return resources[0]

    except Exception as e:
        print(f"❌ Error querying device ID for {hostname}: {e}")
        return None

def get_os(device_id):
    try:
        response = falcon.get_device_details(ids=[device_id])
        #print (response)
        if response.get("status_code") == 200:
            platform = response["body"]["resources"][0]['platform_name'].lower()
            if "windows" in platform:
                return "windows"
            elif "mac" in platform:
                return "macos"
            elif "linux" in platform:
                return "linux"
        else:
            print(f"⚠️ Could not determine OS for device ID {device_id}")
    except Exception as e:
        print(f"❌ Error fetching OS for device ID {device_id}: {e}")
    return "unknown"

def build_tag(dept, location, os_type):
    return f"{dept}_{location}_{os_type}_endpoint".lower()

def tag_device(device_id, tag):
    try:
        response = falcon.update_device_tags(action_name="add", ids=[device_id], tags=tag)
        print (response)
        if response.get("status_code") in [200, 201, 202]:
            return True
        else:
            print(f"🔴 API failed to tag device {device_id}: {response}")
    except Exception as e:
        print(f"❌ Exception while tagging device {device_id}: {e}")
    return False

# ---------- MAIN ----------
if __name__ == "__main__":
    csv_path = "hosts.csv"
    host_rows = read_host_data(csv_path)

    for row in host_rows:
        try:
            hostname = row["host"].strip()
            dept = row.get("department", "").strip()
            location = row.get("location", "").strip()

            if not hostname or not dept or not location:
                print(f"⚠️ Missing fields for row: {row}")
                continue
            
            
            print(f"\n🔍 Processing host: {hostname}")
            device_id = get_device_id_by_hostname(hostname)

            if not device_id:
                continue

            os_type = get_os(device_id)
            tag = build_tag(dept, location, os_type)
            print(f"🏷️  Applying tag: {tag}")

            if tag_device(device_id, tag):
                print("✅ Tag applied successfully.")
            else:
                print("❌ Failed to apply tag.")

            time.sleep(1)  # Avoid rate limits

        except Exception as e:
            print(f"❌ Unexpected error for host {row}: {e}")
