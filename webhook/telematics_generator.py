import requests
import random
import time
from datetime import datetime

# ------------------------------------------
# CONFIGURATION
# ------------------------------------------
WEBHOOK_URL = "https://parthmishra272.app.n8n.cloud/webhook-test/telematics-event"
VEHICLE_IDS = [f"VHC{str(i).zfill(3)}" for i in range(1, 11)]  # VHC001 → VHC010

SEND_INTERVAL_SECONDS = 10   # send data every 10 seconds


# ------------------------------------------
# HELPER FUNCTION TO GENERATE RANDOM TELEMATICS
# ------------------------------------------
def generate_telematics(vehicle_id):
    return {
        "vehicle_id": vehicle_id,
        "timestamp": datetime.utcnow().isoformat() + "Z",

        # Engine and performance
        "engine_temp_c": round(random.uniform(70, 110), 2),
        "rpm": random.randint(900, 7000),
        "vehicle_speed_kmph": round(random.uniform(0, 110), 2),

        # Health indicators
        "battery_health_pct": random.randint(60, 100),
        "brake_pad_wear_pct": random.randint(5, 85),
        "oil_pressure_psi": round(random.uniform(20, 70), 2),

        # Air/Coolant sensors
        "coolant_temp_c": round(random.uniform(60, 100), 2),
        "intake_air_temp_c": round(random.uniform(15, 45), 2),

        # Fuel & efficiency
        "fuel_efficiency_kmpl": round(random.uniform(25, 60), 2),

        # DTC codes
        "dtc_code": random.choice(["OK", "P0128", "P0300", "P0420", "OK", "OK"]),

        # GPS (random within India)
        "gps_lat": round(random.uniform(20.0, 28.0), 6),
        "gps_lon": round(random.uniform(72.0, 88.0), 6)
    }


# ------------------------------------------
# MAIN LOOP
# ------------------------------------------
def send_telematics():
    print("Starting live telematics generator...")
    print(f"Sending to webhook: {WEBHOOK_URL}")
    print("Press CTRL+C to stop.\n")

    while True:
        vehicle_id = random.choice(VEHICLE_IDS)
        tele_data = generate_telematics(vehicle_id)

        print(f"Sending telematics for {vehicle_id} → {tele_data['timestamp']}")

        try:
            response = requests.post(WEBHOOK_URL, json=tele_data, timeout=5)
            print(f"Status: {response.status_code}")
        except Exception as e:
            print("Error sending data:", e)

        time.sleep(SEND_INTERVAL_SECONDS)


if __name__ == "__main__":
    send_telematics()
