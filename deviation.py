"""
Deviation Analytics Engine (Shapely & GeoPandas)
Flowchart step 3 -> "Pass Telemetry Frame" arrives here.
Flowchart step 3b -> "Check Spatial Path Buffer (over 50m)" against PostgreSQL+PostGIS.

Two layers, matching the architecture diagram:
  1. A fast in-memory Shapely check (buffer polygon around the planned route),
     useful for the dashboard preview and for unit testing without a DB.
  2. The authoritative PostGIS ST_Distance(geography) check, which is what the
     backend actually trusts to flag a deviation.
"""
from shapely.geometry import Point, LineString
from shapely.ops import transform
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.models import Vehicle
from app.config import settings


def shapely_is_within_buffer(route_coords: list[tuple[float, float]],
                              lat: float, lon: float,
                              buffer_deg: float = 0.00045) -> bool:
    """
    Quick local check using Shapely only (no DB round trip).
    buffer_deg ~ 0.00045 degrees is ~50m at the equator - good enough for a
    fast pre-check before we confirm with PostGIS's real geography math.
    """
    route = LineString(route_coords)
    point = Point(lon, lat)
    return route.buffer(buffer_deg).contains(point)


def postgis_distance_from_route_m(db: Session, vehicle: Vehicle, lat: float, lon: float) -> float:
    """
    Authoritative check: real-world distance (metres) from the vehicle's
    current point to its planned_route LineString, using PostGIS geography
    math (accounts for the Earth's curvature, unlike raw Shapely degrees).
    """
    point_wkt = f"SRID=4326;POINT({lon} {lat})"
    result = db.execute(
        select(
            func.ST_Distance(
                func.ST_GeogFromWKB(vehicle.planned_route),
                func.ST_GeogFromText(point_wkt),
            )
        )
    ).scalar()
    return float(result or 0)


def check_deviation(db: Session, vehicle: Vehicle, lat: float, lon: float) -> tuple[bool, float]:
    """Returns (deviated, distance_m). deviated=True once distance exceeds the
    project's 50m buffer (app.config.settings.deviation_buffer_meters)."""
    distance_m = postgis_distance_from_route_m(db, vehicle, lat, lon)
    return distance_m > settings.deviation_buffer_meters, distance_m
