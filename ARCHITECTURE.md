# Architecture notes

This expands on the table in the root `README.md`, mapping every numbered
step in `flowchart.png` to the exact function that implements it.

## 1. Simulation Layer
**`simulation/telemetry_simulator.py`** — reads `simulation/routes/sample_route.geojson`,
walks it one point at a time, and emits a `telemetry` Socket.IO event every
2 seconds (`INTERVAL_SECONDS`). After a few pings it deliberately drifts the
point sideways to simulate the "virtual roadblock" / traffic jam from your
scenario slide.

## 2. WebSocket Streamer → Broadcast / Sync
**`backend/app/sockets.py :: handle_telemetry`** receives the frame, updates
the vehicle's `current_position` in PostGIS, and re-broadcasts it as
`position_update` to both the `operators` room (dashboard) and the `drivers`
room (driver PWA) — steps 2a and 2b in the diagram.

## 3. Deviation Analytics Engine
**`backend/app/services/deviation.py`**
- `shapely_is_within_buffer` — a quick, dependency-free Shapely check.
- `postgis_distance_from_route_m` — the authoritative check, using
  `ST_Distance` on a PostGIS `geography` (curved-earth accurate, unlike raw
  Shapely degrees). This is the "Check Spatial Path Buffer (over 50 m)"
  arrow in the diagram.

## 4. Local OSRM Engine
**`backend/app/services/routing.py :: get_detour_route`** calls OSRM's
`/route/v1/driving/...` endpoint and returns a GeoJSON `LineString` plus the
new ETA. By default it points at the free public demo server
(`https://router.project-osrm.org`) so the whole project runs with **no
extra downloads**.

### Making it a truly *local* OSRM engine
1. Pick a small city extract from Geofabrik, e.g.
   `https://download.geofabrik.de/asia/india/karnataka-latest.osm.pbf`
   (this is the one-time ~150 MB download the diagram's "local shortest
   path" implies — not something to commit to Git; it's in `.gitignore`).
2. Put it at `osrm-data/map.osm.pbf`, then run the standard OSRM prep steps:
   ```bash
   docker run -t -v "$(pwd)/osrm-data:/data" osrm/osrm-backend osrm-extract -p /opt/car.lua /data/map.osm.pbf
   docker run -t -v "$(pwd)/osrm-data:/data" osrm/osrm-backend osrm-partition /data/map.osrm
   docker run -t -v "$(pwd)/osrm-data:/data" osrm/osrm-backend osrm-customize /data/map.osrm
   ```
3. `docker compose --profile local-osrm up -d osrm`
4. Set `OSRM_BASE_URL=http://localhost:5000` in `backend/.env`.

## 5. Gemini AI Flash Model
**`backend/app/services/ai_explain.py :: explain_deviation`** — sends the
deviation distance, cause and detour ETA to Gemini and returns the two-line
explanation shown on the decision card. Falls back to a template string if
`GEMINI_API_KEY` isn't set, so the rest of the demo still works.

## 6. Decision Card → Control Room Operator
**`dashboard/src/components/DecisionCard.jsx`** renders the explanation and
the Approve/Override buttons, which emit `operator_decision` back to the
backend (**`sockets.py :: handle_operator_decision`**).

## 7. Mobile Driver PWA guidance
On `APPROVED`, the backend emits `route_update` to the `drivers` room.
**`driver-pwa/src/pages/DriverView.jsx`** draws the new path and speaks the
instruction aloud with the browser's built-in Web Speech API.

## 8. Proximity Alert Engine → Civilian push
**`backend/app/services/proximity.py :: find_nearby_civilian_tokens`** runs
`ST_DWithin` against every registered `CivilianDevice` within 500 m
(`CIVILIAN_ALERT_RADIUS_METERS`), and the backend emits `yield_warning`
straight to each of those socket sessions.
**`driver-pwa/src/pages/CivilianView.jsx`** is the receiving end.

---

## Deployment walkthrough (all free tiers)

### Database → Neon (or Supabase)
1. Create a free Postgres project at https://neon.tech.
2. In the SQL editor, run `CREATE EXTENSION IF NOT EXISTS postgis;`
3. Copy the connection string into your deployed backend's `DATABASE_URL`
   (use the `postgresql+psycopg://...` form, same as `.env.example`).

### Backend → Render
1. Push this repo to GitHub (see root README §2).
2. On https://render.com → New → Web Service → connect the repo, root
   directory `backend/`.
3. Build command: `pip install -r requirements.txt`
   Start command: `uvicorn app.main:socket_app --host 0.0.0.0 --port $PORT`
4. Add environment variables from `backend/.env.example` (with your real
   `DATABASE_URL`, `GEMINI_API_KEY`, and `ALLOWED_ORIGINS` set to your
   deployed frontend URLs).
5. Render's free web services support WebSockets, so Socket.IO works as-is.

### Dashboard & Driver PWA → Vercel
1. New Project → import the same GitHub repo.
2. Root directory: `dashboard/` (repeat as a second Vercel project with root
   directory `driver-pwa/`).
3. Framework preset: Vite. Add `VITE_MAPBOX_TOKEN` and `VITE_SOCKET_URL`
   (your Render backend's HTTPS URL) as environment variables.
4. Deploy — Vercel builds `npm run build` and serves `dist/` automatically,
   over HTTPS, which is required for the driver PWA to be installable and
   for `navigator.geolocation` to work on most mobile browsers.

### OSRM
Keep using the public demo server for the deployed demo unless you need the
fully local engine — running your own OSRM instance in production means
hosting the map extract too, which is more infrastructure than a college
demo typically needs.
