from typing import Optional
from pydantic import BaseModel


class TelemetryFrame(BaseModel):
    """Step 1/3: one GPS ping from the telemetry simulator."""
    call_sign: str
    lat: float
    lon: float
    speed_kmh: Optional[float] = None


class CivilianPing(BaseModel):
    token: str
    lat: float
    lon: float


class OperatorDecision(BaseModel):
    """Step 6 → operator clicks Approve Reroute / Override on the dashboard."""
    vehicle_id: int
    deviation_log_id: int
    decision: str  # "APPROVED" | "OVERRIDDEN"
