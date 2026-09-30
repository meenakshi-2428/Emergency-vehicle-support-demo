"""
Python Telemetry Script (Simulation Layer)
Flowchart step 1: "Live GPS Telemetry (2s Stream)" -> WebSocket Streamer.

Walks the ambulance along simulation/routes/sample_route.geojson one point
every 2 seconds. Partway through, it simulates a "virtual roadblock" by
jumping sideways off the planned path - matching the scenario slide
("Gridlock ahead" -> "Deviation detected"), which is what triggers the
backend's deviation -> OSRM -> Gemini -> decision-card pipeline.
"""
import asyncio
import json
import pathlib
import socketio

BACKEND_URL = "http://localhost:8000"
CALL_SIGN = "Ambulance #102"
INTERVAL_SECONDS = 2
ROADBLOCK_AFTER_STEP = 3          # after this many pings, "hit gridlock" and drift off-route
ROADBLOCK_OFFSET_DEG = 0.0009     # ~100m sideways - safely past the 50m deviation buffer

ROUTE_FILE = pathlib.Path(__file__).parent / "routes" / "sample_route.geojson"

sio = socketio.AsyncClient()


def densify(coords, points_per_segment=4):
    """Turn the sparse route into more, closer-together points so a 2s
    interval feels like a real drive rather than teleporting between nodes."""
    dense = []
    for (lon1, lat1), (lon2, lat2) in zip(coords, coords[1:]):
        for i in range(points_per_segment):
            t = i / points_per_segment
            dense.append((lon1 + (lon2 - lon1) * t, lat1 + (lat2 - lat1) * t))
    dense.append(coords[-1])
    return dense


async def main():
    with open(ROUTE_FILE) as f:
        route = json.load(f)
    coords = densify(route["geometry"]["coordinates"])

    await sio.connect(BACKEND_URL)
    print(f"Connected to {BACKEND_URL}. Streaming {CALL_SIGN} telemetry every {INTERVAL_SECONDS}s...")

    for step, (lon, lat) in enumerate(coords):
        if step == ROADBLOCK_AFTER_STEP:
            print(">> Simulating traffic jam / road closure event - drifting off planned route")
            lon += ROADBLOCK_OFFSET_DEG
            lat += ROADBLOCK_OFFSET_DEG

        payload = {"call_sign": CALL_SIGN, "lat": lat, "lon": lon, "speed_kmh": 22}
        await sio.emit("telemetry", payload)
        print(f"  sent frame {step + 1}/{len(coords)}: lat={lat:.5f} lon={lon:.5f}")
        await asyncio.sleep(INTERVAL_SECONDS)

    print("Route complete. Disconnecting.")
    await sio.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
