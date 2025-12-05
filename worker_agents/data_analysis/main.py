from fastapi import FastAPI, Query
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

from worker_agents.data_analysis.agent_logic import analyze_vehicle_telematics
from datetime import datetime



# ============================================================
# JSON CLEANER (reuse same as in tools)
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
# FASTAPI APP INITIALIZATION
# ============================================================

app = FastAPI(
    title="Data Analysis Agent",
    description="Real-time Vehicle Telematics Processor",
    version="1.0.0"
)

# Optional - Allow n8n + Cloudflare to call API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# REQUEST MODEL
# ============================================================

class AnalyzeRequest(BaseModel):
    vehicle_id: str


# ============================================================
# ROOT ENDPOINT (Health Check)
# ============================================================

@app.get("/")
def root():
    return {
        "message": "Data Analysis Agent active",
        "status": "running",
        "endpoints": {
            "POST": "/analyze",
            "GET": "/analyze?vehicle_id=<id>"
        }
    }


# ============================================================
# POST ENDPOINT (Used by n8n + internal Master Agent)
# ============================================================

@app.post("/analyze")
def analyze_post(req: AnalyzeRequest):
    vehicle_id = req.vehicle_id.strip()

    result = analyze_vehicle_telematics(vehicle_id)
    return clean_json(result)


# ============================================================
# GET ENDPOINT (Used for browser testing)
# ============================================================

@app.get("/analyze")
def analyze_get(vehicle_id: str = Query(..., description="Vehicle ID to analyze")):

    vehicle_id = vehicle_id.strip()

    result = analyze_vehicle_telematics(vehicle_id)
    return clean_json(result)


# ============================================================
# RUN SERVER (for local debugging)
# ============================================================
# Run using:
# uvicorn main:app --reload --host 0.0.0.0 --port 8000

