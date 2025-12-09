import requests
import uuid
import random
import json
from datetime import datetime

from service_center_slots_loader import pick_service_center
from telematics_loader import get_random_vehicle


# ------------------------------------------------------
# SET YOUR N8N WEBHOOK URL HERE
# ------------------------------------------------------
N8N_WEBHOOK_URL = "https://parthmishra272.app.n8n.cloud/webhook-test/service-completed"
# Example: "https://mydomain.com/webhook/service-completed"
# ------------------------------------------------------


def send_random_service_completed():
    """
    Automatically picks:
      ✔ random vehicle_id from telematics feed
      ✔ city from vehicle_profiles.json
      ✔ appropriate service center from service_center_slots.json
    Then sends event to n8n Workflow B.
    """

    # Pick vehicle from telematics feed
    vehicle_id, city = get_random_vehicle()

    # Pick service center by city if possible
    center_key, center_data = pick_service_center(city)
    service_center_location = center_data["location"]

    # Generate a random service ID
    service_id = "SRV-" + uuid.uuid4().hex[:8].upper()

    payload = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "vehicle_id": vehicle_id,
        "service_id": service_id,
        "service_center": service_center_location,
        "city": city,
        "completed_tasks": [
            "General inspection",
            "Brake cleaning",
            "Oil check & top-up",
            "Chain lubrication"
        ],
        "invoice_amount": random.randint(450, 2500),
        "warranty_applied": random.choice([True, False]),
        "job_card_closed": True,
        "notes": "Automatically generated service close event."
    }

    print("\n📤 Sending Service Completion Payload:")
    print(json.dumps(payload, indent=2))

    try:
        resp = requests.post(
            N8N_WEBHOOK_URL,
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        print("\n🔄 Response Status:", resp.status_code)
        print("🔎 Response Body:", resp.text)

    except Exception as e:
        print("\n❌ Failed to send webhook event:", str(e))


if __name__ == "__main__":
    print("🚀 Triggering Service Completed Event...")
    send_random_service_completed()
