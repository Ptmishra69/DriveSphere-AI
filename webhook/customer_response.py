import requests
import json

WEBHOOK_URL = "https://parthmishra272.app.n8n.cloud/webhook-test/customer-response"

def send_customer_response(vehicle_id, timestamp, accepted=True,
                           preferred_date="2025-01-26",
                           preferred_time_band="morning"):

    payload = {
        "vehicle_id": vehicle_id,
        "timestamp": timestamp,
        "accepted": accepted,
        "preferred_date": preferred_date,
        "preferred_time_band": preferred_time_band
    }

    print("➡ Sending payload:")
    print(json.dumps(payload, indent=2))

    try:
        response = requests.post(WEBHOOK_URL, json=payload, timeout=5)
        print("\nStatus:", response.status_code)
        print("Response:", response.text)

    except Exception as e:
        print("❌ Error sending request:", e)


# 🔥 EXAMPLE USAGE ------------------------------------------
# These two values will come from Workflow 1
vehicle_id_from_workflow_1 = "VHC001"
timestamp_from_workflow_1   = "2025-01-24T10:15:22Z"

send_customer_response(
    vehicle_id=vehicle_id_from_workflow_1,
    timestamp=timestamp_from_workflow_1
)
