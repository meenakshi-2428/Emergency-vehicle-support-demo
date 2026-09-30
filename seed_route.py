"""
Run once after the DB is up:  python -m app.seed_route
Loads simulation/routes/sample_route.geojson into PostGIS as the planned
route for the demo vehicle, so the Deviation Analytics Engine has something
to compare live telemetry against.
"""
import json
import pathlib

from app.database import SessionLocal, engine, Base, init_postgis
from app.models import Vehicle

ROUTE_FILE = pathlib.Path(__file__).resolve().parents[2] / "simulation" / "routes" / "sample_route.geojson"


def main():
    with engine.begin() as conn:
        init_postgis(conn)
        Base.metadata.create_all(bind=conn)

    with open(ROUTE_FILE) as f:
        feature = json.load(f)

    call_sign = feature["properties"]["call_sign"]
    coords = feature["geometry"]["coordinates"]  # list of [lon, lat]
    linestring_wkt = "LINESTRING(" + ", ".join(f"{lon} {lat}" for lon, lat in coords) + ")"
    start_lon, start_lat = coords[0]

    db = SessionLocal()
    try:
        vehicle = db.query(Vehicle).filter_by(call_sign=call_sign).first()
        if vehicle is None:
            vehicle = Vehicle(call_sign=call_sign)
            db.add(vehicle)
        vehicle.planned_route = f"SRID=4326;{linestring_wkt}"
        vehicle.current_position = f"SRID=4326;POINT({start_lon} {start_lat})"
        vehicle.status = "EN_ROUTE"
        db.commit()
        print(f"Seeded planned route for {call_sign} ({len(coords)} points).")
    finally:
        db.close()


if __name__ == "__main__":
    main()
