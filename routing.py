"""
Local OSRM Engine client
Flowchart step 4 -> "Trigger Dynamic Detour Path"

Defaults to the free public OSRM demo server so the project runs with zero
extra setup. Point OSRM_BASE_URL at http://localhost:5000 once you run the
optional local-osrm docker-compose profile (see docs/ARCHITECTURE.md §4) for
a true "local shortest path" engine, as named in the architecture diagram.
"""
import httpx

from app.config import settings


async def get_detour_route(from_lat: float, from_lon: float,
                            to_lat: float, to_lon: float) -> dict:
    """
    Calls OSRM's /route service and returns:
      { "geometry": GeoJSON LineString, "distance_m": float, "duration_s": float }
    """
    url = (
        f"{settings.osrm_base_url}/route/v1/driving/"
        f"{from_lon},{from_lat};{to_lon},{to_lat}"
        "?overview=full&geometries=geojson"
    )
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        data = resp.json()

    if not data.get("routes"):
        raise ValueError(f"OSRM returned no route: {data}")

    route = data["routes"][0]
    return {
        "geometry": route["geometry"],          # GeoJSON LineString - feed straight to Mapbox GL
        "distance_m": route["distance"],
        "duration_s": route["duration"],
    }
