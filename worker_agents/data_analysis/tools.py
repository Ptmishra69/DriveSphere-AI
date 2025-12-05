from langchain.tools import tool
from shared.shared_loader import (
    load_vehicle_profile,
    load_maintenance_history,
    load_telematics
)
from shared.shared_loader import (load_vehicle_profile, load_maintenance_history, load_telematics)

from datetime import datetime


# ============================================================
# JSON SANITIZER — Ensures datetime is serializable
# ============================================================

def clean_json(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, dict):
        return {k: clean_json(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [clean_json(i) for i in obj]
    return obj


# ============================================================
# UTIL — Direct vehicle_id validation
# ============================================================

def validate_vehicle_id(vehicle_id):
    """
    Tools now accept a plain string: tool.run("VHC001")
    This validator ensures we always get a proper clean string.
    """
    if not vehicle_id or not isinstance(vehicle_id, str):
        return None
    return vehicle_id.strip()



# ============================================================
# VEHICLE PROFILE TOOL
# ============================================================

@tool("get_vehicle_profile")
def get_vehicle_profile(vehicle_id: str):
    """
    Returns clean vehicle profile.
    LangChain calls this tool as:
    get_vehicle_profile.run("VHC001")
    """

    vehicle_id = validate_vehicle_id(vehicle_id)

    if not vehicle_id:
        return {
            "exists": False,
            "vehicle_id": None,
            "error": "Invalid or missing vehicle_id"
        }

    try:
        profile = load_vehicle_profile(vehicle_id)

        if "error" in profile:
            return {
                "exists": False,
                "vehicle_id": vehicle_id,
                "error": profile["error"]
            }

        return {
            "exists": True,
            "vehicle_id": vehicle_id,
            "profile": clean_json(profile)
        }

    except Exception as e:
        return {
            "exists": False,
            "vehicle_id": vehicle_id,
            "error": str(e)
        }



# ============================================================
# MAINTENANCE HISTORY / USAGE TOOL
# ============================================================

@tool("get_historical_usage")
def get_historical_usage(vehicle_id: str):
    """
    Returns historical usage summary + maintenance patterns.
    Called via:
    get_historical_usage.run("VHC001")
    """

    vehicle_id = validate_vehicle_id(vehicle_id)

    if not vehicle_id:
        return {
            "exists": False,
            "vehicle_id": None,
            "error": "Invalid or missing vehicle_id"
        }

    try:
        history = load_maintenance_history(vehicle_id)

        if not history:
            return {
                "exists": False,
                "vehicle_id": vehicle_id,
                "total_records": 0,
                "recurring_issues": [],
                "declined_repairs": 0,
                "last_service_date": None
            }

        summary = {
            "exists": True,
            "vehicle_id": vehicle_id,
            "total_records": len(history),
            "recurring_issues": [],
            "declined_repairs": 0,
            "last_service_date": None,
        }

        for h in history:

            if (
                isinstance(h.get("issue_reported"), str)
                and "recurring" in h["issue_reported"].lower()
            ):
                summary["recurring_issues"].append(h["issue_reported"])

            if h.get("customer_declined_parts_replacement"):
                summary["declined_repairs"] += 1

            if h.get("date") and isinstance(h["date"], datetime):
                summary["last_service_date"] = h["date"].isoformat()

        return clean_json(summary)

    except Exception as e:
        return {
            "exists": False,
            "vehicle_id": vehicle_id,
            "error": str(e)
        }



# ============================================================
# LIVE TELEMATICS TOOL
# ============================================================

@tool("get_telematics_snapshot")
def get_telematics_snapshot(vehicle_id: str):
    """
    Returns the *latest* telematics snapshot.
    Called as:
    get_telematics_snapshot.run("VHC001")
    """

    vehicle_id = validate_vehicle_id(vehicle_id)

    if not vehicle_id:
        return {
            "exists": False,
            "vehicle_id": None,
            "error": "Invalid or missing vehicle_id"
        }

    try:
        telematics = load_telematics(vehicle_id)

        if "error" in telematics:
            return {
                "exists": False,
                "vehicle_id": vehicle_id,
                "error": telematics["error"]
            }

        telematics["exists"] = True
        return clean_json(telematics)

    except Exception as e:
        return {
            "exists": False,
            "vehicle_id": vehicle_id,
            "error": str(e)
        }
