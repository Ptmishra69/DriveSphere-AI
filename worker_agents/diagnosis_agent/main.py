# main.py
from fastapi import FastAPI
from pydantic import BaseModel
from .agent_logic import diagnose_vehicle
import uvicorn

app = FastAPI(title="Diagnosis Agent", version="1.0.0")

class DiagnoseRequest(BaseModel):
    vehicle_id: str

@app.post("/diagnose")
def diagnose(req: DiagnoseRequest):
    """
    Diagnose endpoint expects a vehicle_id and returns a JSON diagnosis object.
    """
    result = diagnose_vehicle(req.vehicle_id)
    return result

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8002, reload=True)
