# tools.py
import json
import os
from datetime import datetime
from typing import List, Dict, Any

LOG_PATH = os.path.join("..", "..", "data", "agent_activity_logs.json")
ALERT_PATH = os.path.join("..", "..", "data", "ueba_alerts.json")

def _ensure_file(path: str, default):
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(default, f, indent=2)

def append_activity_log(record: Dict[str, Any]):
    _ensure_file(LOG_PATH, [])
    with open(LOG_PATH, "r+", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            data = []
        data.append(record)
        f.seek(0)
        json.dump(data, f, indent=2)
        f.truncate()
    return {"status": "ok", "count": len(data)}

def read_activity_logs() -> List[Dict[str, Any]]:
    _ensure_file(LOG_PATH, [])
    with open(LOG_PATH, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def append_alert(alert: Dict[str, Any]):
    _ensure_file(ALERT_PATH, [])
    with open(ALERT_PATH, "r+", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            data = []
        data.append(alert)
        f.seek(0)
        json.dump(data, f, indent=2)
        f.truncate()
    return {"status": "alert_stored", "count": len(data)}

def read_alerts() -> List[Dict[str, Any]]:
    _ensure_file(ALERT_PATH, [])
    with open(ALERT_PATH, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []
