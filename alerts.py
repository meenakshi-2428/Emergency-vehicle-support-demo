from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import DeviationLog

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


@router.get("")
def list_deviation_logs(db: Session = Depends(get_db)):
    """The Alert Center feed on the dashboard - every deviation detected so far."""
    logs = db.query(DeviationLog).order_by(DeviationLog.detected_at.desc()).limit(50).all()
    return [
        {
            "id": log.id,
            "vehicle_id": log.vehicle_id,
            "distance_from_route_m": log.distance_from_route_m,
            "cause": log.cause,
            "delay_prediction_minutes": log.delay_prediction_minutes,
            "ai_explanation": log.ai_explanation,
            "operator_decision": log.operator_decision,
            "detected_at": log.detected_at.isoformat() if log.detected_at else None,
        }
        for log in logs
    ]
