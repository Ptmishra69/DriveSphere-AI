from fastapi import FastAPI
from pydantic import BaseModel
from agent_logic import generate_engagement

app = FastAPI(
    title="Customer Engagement Agent (UEBA-powered)",
    version="2.0"
)

class EngagementRequest(BaseModel):
    vehicle_id: str


@app.post("/engage")
def engage(req: EngagementRequest):
    return generate_engagement(req.vehicle_id)
