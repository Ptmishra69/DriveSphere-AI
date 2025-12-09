# main.py

from fastapi import FastAPI
from pydantic import BaseModel
from .agent_logic import generate_manufacturing_insights

app = FastAPI(
    title="RCA/CAPA Agent",
    version="1.0.0",
    description="Offline RCA agent without external dependencies"
)


class RCARequest(BaseModel):
    vehicle_id: str
    service_event: dict
    feedback_analysis: dict


@app.post("/rca")
def rca(req: RCARequest):
    return generate_manufacturing_insights(
        req.vehicle_id,
        req.service_event,
        req.feedback_analysis
    )
