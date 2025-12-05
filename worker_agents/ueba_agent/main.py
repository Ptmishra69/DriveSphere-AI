# main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Any, Dict
from tools import append_activity_log, read_activity_logs, read_alerts
from agent_logic import scan_and_detect

app = FastAPI(title="UEBA Agent", version="1.0.0")

class ActivityRecord(BaseModel):
    timestamp: str
    agent_name: str
    agent_id: str
    action: str
    endpoint: str
    target_resource: str
    status_code: int
    payload_size: int = 0
    latency_ms: int = 0
    extra: Dict[str, Any] = {}

@app.post("/ingest")
def ingest(record: ActivityRecord):
    # Basic validation
    rec = record.dict()
    # Normalize timestamp to ISO (assuming client sends ISO)
    try:
        append_activity_log(rec)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"status": "ingested"}

@app.post("/scan")
def run_scan(window_minutes: int = 15):
    alerts = scan_and_detect(window_minutes=window_minutes)
    return {"alerts_count": len(alerts), "alerts": alerts}

@app.get("/alerts")
def get_alerts():
    return read_alerts()

@app.get("/logs")
def get_logs():
    return read_activity_logs()
