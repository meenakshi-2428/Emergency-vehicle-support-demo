"""
Proximity Alert Engine (ST_DWithin)
Flowchart step 8 -> "Push Geofenced Yield Warning" to any Civilian Driver
inside the alert radius, after "Query Civilian Tokens in 500m Radius"
against PostgreSQL+PostGIS.
"""
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.models import CivilianDevice
from app.config import settings


def find_nearby_civilian_tokens(db: Session, lat: float, lon: float) -> list[str]:
    """Returns the socket tokens of every civilian device within the
    project's 500m geofence (settings.civilian_alert_radius_meters)."""
    point_wkt = f"SRID=4326;POINT({lon} {lat})"
    rows = db.execute(
        select(CivilianDevice.token).where(
            func.ST_DWithin(
                func.ST_GeogFromWKB(CivilianDevice.last_position),
                func.ST_GeogFromText(point_wkt),
                settings.civilian_alert_radius_meters,
            )
        )
    ).all()
    return [r[0] for r in rows]


def upsert_civilian_position(db: Session, token: str, lat: float, lon: float) -> CivilianDevice:
    point_wkt = f"SRID=4326;POINT({lon} {lat})"
    device = db.query(CivilianDevice).filter_by(token=token).first()
    if device is None:
        device = CivilianDevice(token=token, last_position=point_wkt)
        db.add(device)
    else:
        device.last_position = point_wkt
    db.commit()
    db.refresh(device)
    return device
