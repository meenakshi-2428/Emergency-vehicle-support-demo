"""
WebSocket Streamer (Socket.io)
This file is the spine of the flowchart: every numbered step 1-8 that isn't a
plain REST call passes through here.

Rooms:
  "operators"  - Laptop Admin Dashboard clients (Control Room Operator)
  "drivers"    - Mobile Driver PWA clients
  civilian devices join no room; they're targeted individually by their
  socket session id (sid), which doubles as their "civilian token".
"""
import asyncio
import socketio

from app.database import SessionLocal
from app.models import Vehicle, DeviationLog
from app.services.deviation import check_deviation
from app.services.routing import get_detour_route
from app.services.ai_explain import explain_deviation
from app.services.proximity import find_nearby_civilian_tokens, upsert_civilian_position
from app.config import settings

sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins=settings.cors_origins)


# ---------------------------------------------------------------- connections
@sio.event
async def connect(sid, environ, auth):
    print(f"[socket] client connected: {sid}")


@sio.event
async def disconnect(sid):
    print(f"[socket] client disconnected: {sid}")


@sio.on("register_operator")
async def register_operator(sid, data):
    sio.enter_room(sid, "operators")


@sio.on("register_driver")
async def register_driver(sid, data):
    sio.enter_room(sid, "drivers")


@sio.on("register_civilian")
async def register_civilian(sid, data):
    """Civilian app sends its location periodically; sid is its token."""
    lat, lon = data["lat"], data["lon"]

    def _save():
        db = SessionLocal()
        try:
            upsert_civilian_position(db, token=sid, lat=lat, lon=lon)
        finally:
            db.close()

    await asyncio.to_thread(_save)


# --------------------------------------------------------------- step 1 -> 8
@sio.on("telemetry")
async def handle_telemetry(sid, data):
    """
    Step 1: Live GPS Telemetry arrives from the Python Telemetry Script.
    Step 2: Broadcast Live Position / Sync Navigation Route.
    Step 3: Pass Telemetry Frame -> Deviation Analytics Engine.
    """
    call_sign = data["call_sign"]
    lat, lon = data["lat"], data["lon"]

    def _load_and_check():
        db = SessionLocal()
        try:
            vehicle = db.query(Vehicle).filter_by(call_sign=call_sign).first()
            if vehicle is None:
                return None, False, 0.0
            vehicle.current_position = f"SRID=4326;POINT({lon} {lat})"
            db.commit()
            deviated, distance_m = check_deviation(db, vehicle, lat, lon)
            return vehicle.id, deviated, distance_m
        finally:
            db.close()

    vehicle_id, deviated, distance_m = await asyncio.to_thread(_load_and_check)
    if vehicle_id is None:
        print(f"[socket] unknown vehicle '{call_sign}', ignoring telemetry frame")
        return

    # Step 2: Broadcast Live Position -> dashboard, and Sync Navigation Route -> driver
    position_payload = {"call_sign": call_sign, "lat": lat, "lon": lon, "distance_m": distance_m}
    await sio.emit("position_update", position_payload, room="operators")
    await sio.emit("position_update", position_payload, room="drivers")

    if not deviated:
        return

    await _run_deviation_pipeline(vehicle_id, call_sign, lat, lon, distance_m)


async def _run_deviation_pipeline(vehicle_id: int, call_sign: str,
                                   lat: float, lon: float, distance_m: float):
    """
    Step 4: Trigger Dynamic Detour Path (OSRM).
    Step 5: Request AI Delay Explanation & Action (Gemini).
    Step 6: Display AI Decision Card & Delay Reason -> dashboard.
    """
    def _get_destination():
        """The planned route's last point (ST_EndPoint) is the ambulance's
        original destination - that's what OSRM should route the detour to."""
        import sqlalchemy as sa
        from geoalchemy2.functions import ST_EndPoint, ST_Y, ST_X
        db = SessionLocal()
        try:
            vehicle = db.query(Vehicle).get(vehicle_id)
            end_lat, end_lon = db.execute(
                sa.select(ST_Y(ST_EndPoint(vehicle.planned_route)),
                          ST_X(ST_EndPoint(vehicle.planned_route)))
            ).one()
            return float(end_lat), float(end_lon)
        finally:
            db.close()

    dest_lat, dest_lon = await asyncio.to_thread(_get_destination)
    detour = await get_detour_route(lat, lon, dest_lat, dest_lon)
    detour_min = detour["duration_s"] / 60

    explanation = explain_deviation(
        call_sign=call_sign, distance_m=distance_m, cause="Traffic/road closure ahead",
        delay_min=12, detour_min=detour_min,
    )

    def _log():
        db = SessionLocal()
        try:
            log = DeviationLog(
                vehicle_id=vehicle_id, distance_from_route_m=distance_m,
                cause="Traffic/road closure ahead", delay_prediction_minutes=12,
                ai_explanation=explanation,
            )
            db.add(log)
            vehicle = db.query(Vehicle).get(vehicle_id)
            vehicle.status = "DEVIATED"
            db.commit()
            db.refresh(log)
            return log.id
        finally:
            db.close()

    deviation_log_id = await asyncio.to_thread(_log)

    await sio.emit("decision_card", {
        "vehicle_id": vehicle_id,
        "deviation_log_id": deviation_log_id,
        "call_sign": call_sign,
        "distance_m": distance_m,
        "explanation": explanation,
        "detour_geometry": detour["geometry"],
        "detour_minutes": round(detour_min, 1),
    }, room="operators")


@sio.on("operator_decision")
async def handle_operator_decision(sid, data):
    """
    Step 6 (continued): operator clicks Approve Reroute / Override.
    Step 7: View Path & Audio Guidance -> Mobile Driver PWA.
    Step 8: Push Geofenced Yield Warning -> Civilian Driver.
    """
    vehicle_id = data["vehicle_id"]
    decision = data["decision"]          # "APPROVED" | "OVERRIDDEN"
    detour_geometry = data.get("detour_geometry")
    lat, lon = data["lat"], data["lon"]

    def _update():
        db = SessionLocal()
        try:
            log = db.query(DeviationLog).get(data["deviation_log_id"])
            if log:
                log.operator_decision = decision
            vehicle = db.query(Vehicle).get(vehicle_id)
            if vehicle and decision == "APPROVED" and detour_geometry:
                from shapely.geometry import shape
                vehicle.detour_route = shape(detour_geometry).wkt
                vehicle.status = "REROUTED"
            db.commit()
        finally:
            db.close()

    await asyncio.to_thread(_update)

    if decision != "APPROVED":
        return

    # Step 7
    await sio.emit("route_update", {
        "vehicle_id": vehicle_id,
        "detour_geometry": detour_geometry,
        "instruction": "New route accepted, turn right",
    }, room="drivers")

    # Step 8
    def _find_nearby():
        db = SessionLocal()
        try:
            return find_nearby_civilian_tokens(db, lat, lon)
        finally:
            db.close()

    nearby_tokens = await asyncio.to_thread(_find_nearby)
    for token in nearby_tokens:
        await sio.emit("yield_warning", {
            "message": "⚠️ Emergency Vehicle Approaching! Yield Right Lane.",
        }, to=token)
    print(f"[socket] pushed yield warning to {len(nearby_tokens)} nearby civilian devices")
