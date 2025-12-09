from datetime import datetime, timedelta

def prioritize_slots(centers: dict, urgency: str):
    """
    Sort slots depending on urgency level.
    """
    slots = []

    for center_name, info in centers.items():
        for slot in info["slots"]:
            dt = datetime.strptime(slot, "%Y-%m-%d %H:%M")
            slots.append({
                "center": center_name,
                "location": info["location"],
                "slot": slot,
                "datetime": dt
            })

    slots.sort(key=lambda x: x["datetime"])

    if urgency == "high":
        return slots[:2]
    elif urgency == "medium":
        cutoff = datetime.now() + timedelta(days=3)
        return [s for s in slots if s["datetime"] < cutoff][:3]
    else:
        return slots[:3]
