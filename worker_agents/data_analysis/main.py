# main.py

from fastapi import FastAPI
from pydantic import BaseModel
from .agent_logic import analyze_vehicle_telematics

app = FastAPI(
    title="Data Analysis Agent",
    description="Real-time telematics anomaly detection agent",
    version="1.0.0"
)


class RequestBody(BaseModel):
    vehicle_id: str


@app.post("/analyze")
def analyze(data: RequestBody):
    """
    Main endpoint for Data Analysis Agent.
    """
    result = analyze_vehicle_telematics(data.vehicle_id)
    return result
