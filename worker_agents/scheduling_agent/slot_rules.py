# slot_rules.py

from datetime import datetime, timedelta

def prioritize_slots(centers: dict, urgency: str):
    prioritized = []

    for name, info in centers.items():
        for slot in info["slots"]:
            dt = datetime.strptime(slot, "%Y-%m-%d %H:%M")

            prioritized.append({
                "center": name,
                "location": info["location"],
                "slot": slot,
                "datetime": dt
            })

    prioritized.sort(key=lambda x: x["datetime"])

    if urgency == "high":
        return prioritized[:2]

    elif urgency == "medium":
        cutoff = datetime.now() + timedelta(days=3)
        return [s for s in prioritized if s["datetime"] < cutoff][:3]

    return prioritized[:3]
