import os, json
from langchain.tools import tool
from shared.shared_loader import load_vehicle_profile

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PAST_FEEDBACK_FILE = os.path.abspath(os.path.join(BASE_DIR, "..", "..", "data", "past_feedback.json"))


@tool("get_vehicle_profile")
def get_vehicle_profile_tool(vehicle_id: str):
    """Returns vehicle profile dictionary."""
    return load_vehicle_profile(vehicle_id)


@tool("get_past_feedback")
def get_past_feedback_tool(vehicle_id: str):
    """Returns past stored feedback (offline JSON)."""
    if not os.path.exists(PAST_FEEDBACK_FILE):
        return {}

    try:
        with open(PAST_FEEDBACK_FILE, "r") as f:
            data = json.load(f)
    except:
        return {}

    return data.get(vehicle_id, {})


@tool("store_feedback")
def store_feedback_tool(data: str):
    """Stores processed feedback into disk."""
    os.makedirs(os.path.dirname(PAST_FEEDBACK_FILE), exist_ok=True)

    new = json.loads(data)

    # Load old data
    try:
        if os.path.exists(PAST_FEEDBACK_FILE):
            with open(PAST_FEEDBACK_FILE, "r") as f:
                past = json.load(f)
        else:
            past = {}
    except:
        past = {}

    past[new["vehicle_id"]] = new

    # Save
    with open(PAST_FEEDBACK_FILE, "w") as f:
        json.dump(past, f, indent=2)

    return {"status": "saved"}
