from datetime import datetime, timezone

from geoalchemy2 import Geometry
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship

from app.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class Vehicle(Base):
    """An emergency vehicle (ambulance) being tracked."""
    __tablename__ = "vehicles"

    id = Column(Integer, primary_key=True)
    call_sign = Column(String, unique=True, index=True)          # e.g. "Ambulance #102"
    status = Column(String, default="EN_ROUTE")                  # EN_ROUTE | DEVIATED | REROUTED
    current_position = Column(Geometry(geometry_type="POINT", srid=4326))
    planned_route = Column(Geometry(geometry_type="LINESTRING", srid=4326))
    detour_route = Column(Geometry(geometry_type="LINESTRING", srid=4326), nullable=True)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    deviations = relationship("DeviationLog", back_populates="vehicle")


class DeviationLog(Base):
    """Step 3 → one row per deviation detected, with the AI's explanation (step 5)."""
    __tablename__ = "deviation_logs"

    id = Column(Integer, primary_key=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"))
    distance_from_route_m = Column(Float)
    cause = Column(String, default="Unknown")
    delay_prediction_minutes = Column(Float, nullable=True)
    ai_explanation = Column(Text, nullable=True)
    operator_decision = Column(String, default="PENDING")        # PENDING | APPROVED | OVERRIDDEN
    detected_at = Column(DateTime(timezone=True), default=utcnow)

    vehicle = relationship("Vehicle", back_populates="deviations")


class CivilianDevice(Base):
    """A registered civilian phone / browser that can receive geofenced yield warnings."""
    __tablename__ = "civilian_devices"

    id = Column(Integer, primary_key=True)
    token = Column(String, unique=True, index=True)              # socket.io session id or push token
    last_position = Column(Geometry(geometry_type="POINT", srid=4326))
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
