from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import DeviationLog

router = APIRouter(prefix="/api/decisions", tags=["decisions"])


@router.get("/pending")
def list_pending(db: Session = Depends(get_db)):
    """Everything still waiting for a Control Room Operator to Approve/Override.
    The dashboard normally acts on the 'decision_card' socket event instead of
    polling this - it's here mainly so you can inspect state with Thunder
    Client / curl while wiring things up."""
    logs = db.query(DeviationLog).filter_by(operator_decision="PENDING").all()
    return [
        {"id": log.id, "vehicle_id": log.vehicle_id, "cause": log.cause,
         "ai_explanation": log.ai_explanation}
        for log in logs
    ]
