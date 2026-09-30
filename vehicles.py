from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from geoalchemy2.shape import to_shape

from app.database import get_db
from app.models import Vehicle

router = APIRouter(prefix="/api/vehicles", tags=["vehicles"])


@router.get("")
def list_vehicles(db: Session = Depends(get_db)):
    vehicles = db.query(Vehicle).all()
    return [
        {
            "id": v.id,
            "call_sign": v.call_sign,
            "status": v.status,
            "position": list(to_shape(v.current_position).coords)[0] if v.current_position else None,
        }
        for v in vehicles
    ]


@router.get("/{vehicle_id}")
def get_vehicle(vehicle_id: int, db: Session = Depends(get_db)):
    vehicle = db.query(Vehicle).get(vehicle_id)
    if not vehicle:
        raise HTTPException(404, "Vehicle not found")
    return {
        "id": vehicle.id,
        "call_sign": vehicle.call_sign,
        "status": vehicle.status,
        "position": list(to_shape(vehicle.current_position).coords)[0] if vehicle.current_position else None,
        "planned_route": list(to_shape(vehicle.planned_route).coords) if vehicle.planned_route else None,
    }
