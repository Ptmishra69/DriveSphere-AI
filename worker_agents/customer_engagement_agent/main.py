# main.py

from fastapi import FastAPI
from pydantic import BaseModel
from .agent_logic import generate_engagement

app = FastAPI(
    title="Customer Engagement Agent",
    description="Generates personalized and persuasive customer messaging.",
    version="1.0.0"
)

class EngagementRequest(BaseModel):
    vehicle_id: str
    diagnosis: dict


@app.post("/engage")
def engage_customer(req: EngagementRequest):
    output = generate_engagement(req.vehicle_id, req.diagnosis)
    return output
