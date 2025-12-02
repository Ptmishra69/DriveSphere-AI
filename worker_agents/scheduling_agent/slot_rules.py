# slot_rules.py

from datetime import datetime, timedelta


def prioritize_slots(centers: dict, urgency: str):
    """
    Rule-based sorting.
    urgency = high → earliest slot
    urgency = medium → next 1-2 days
    urgency = low → customer preference-based
    """
    prioritized = []

    for center_name, info in centers.items():
        for slot in info["slots"]:
            dt = datetime.strptime(slot, "%Y-%m-%d %H:%M")

            prioritized.append({
                "center": center_name,
                "location": info["location"],
                "slot": slot,
                "datetime": dt
            })

    # Sort slots earliest → latest
    prioritized.sort(key=lambda x: x["datetime"])

    if urgency == "high":
        return prioritized[:2]   # earliest 2 slots
    elif urgency == "medium":
        cutoff = datetime.now() + timedelta(days=3)
        return [s for s in prioritized if s["datetime"] < cutoff][:3]
    else:
        return prioritized[:3]   # not urgent → top 3 by default
