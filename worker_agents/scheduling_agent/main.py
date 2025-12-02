# main.py

from fastapi import FastAPI
from pydantic import BaseModel
from .agent_logic import schedule_appointment

app = FastAPI(
    title="Scheduling Agent",
    description="Handles scheduling of appointments based on urgency & slot availability.",
    version="1.0.0"
)

class ScheduleRequest(BaseModel):
    vehicle_id: str
    diagnosis: dict
    customer_preference: dict | None = None


@app.post("/schedule")
def schedule(req: ScheduleRequest):
    output = schedule_appointment(
        req.vehicle_id,
        req.diagnosis,
        req.customer_preference
    )
    return output
