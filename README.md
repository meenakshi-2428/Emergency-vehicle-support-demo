# GeoAgentic Emergency Vehicle Support

A software-only prototype: an ambulance streams GPS every 2 seconds, the backend
detects when it strays more than 50 m from its planned route, asks OSRM for a
detour and Gemini for a plain-language explanation, the control room operator
approves it, the driver's app updates, and civilian phones within 500 m get a
yield warning.

This repo is the code behind the numbered flow in `flowchart.png`:

| # | Step | Where it lives |
|---|------|-----------------|
| 1 | Live GPS Telemetry (2 s stream) | `simulation/telemetry_simulator.py` |
| 2 | Broadcast Live Position / Sync Navigation Route | `backend/app/sockets.py` |
| 3 | Pass Telemetry Frame → Deviation Analytics Engine | `backend/app/services/deviation.py` |
| 3b | Check Spatial Path Buffer (over 50 m) | PostGIS `ST_DWithin`, see `deviation.py` |
| 4 | Trigger Dynamic Detour Path → Local OSRM Engine | `backend/app/services/routing.py` |
| 5 | Request AI Delay Explanation & Action → Gemini | `backend/app/services/ai_explain.py` |
| 6 | Display AI Decision Card | `dashboard/src/components/DecisionCard.jsx` |
| 7 | View Path & Audio Guidance | `driver-pwa/src/pages/DriverView.jsx` |
| 8 | Push Geofenced Yield Warning → Civilian Driver | `backend/app/services/proximity.py`, `driver-pwa/src/pages/CivilianView.jsx` |

More detail on every function: `docs/ARCHITECTURE.md`.

---

## 1. What you need installed on your laptop

| Tool | Why | Link |
|---|---|---|
| **Git** | push/pull this repo | https://git-scm.com/downloads |
| **Python 3.11+** | the FastAPI backend and the telemetry simulator | https://www.python.org/downloads/ |
| **Node.js 20 LTS** (includes npm) | the two React apps | https://nodejs.org |
| **Docker Desktop** | runs PostgreSQL+PostGIS and (optionally) a local OSRM server without installing either by hand | https://www.docker.com/products/docker-desktop/ |
| **VS Code** | editor | https://code.visualstudio.com |

You do **not** need to install PostgreSQL or OSRM directly — Docker Compose
handles both. You do need free API keys (below).

### Free accounts / keys you need
- **Google AI Studio** → a free Gemini API key (used for "Explanation" / Gemini AI Flash). https://aistudio.google.com/app/apikey
- **Mapbox** → a free public token, for the two map views. https://account.mapbox.com/access-tokens/ (50k loads/month free, matches your slide 7)

### Recommended VS Code extensions
Install these from the Extensions panel (`Ctrl+Shift+X` / `Cmd+Shift+X`):
- **Python** (ms-python.python) + **Pylance** — backend editing, autocomplete
- **ESLint** (dbaeumer.vscode-eslint) — React linting
- **Prettier — Code formatter** (esbenp.prettier-vscode) — formatting for JS/JSX
- **ES7+ React/Redux/React-Native snippets** (dsznajder.es7-react-js-snippets)
- **Docker** (ms-azuretools.vscode-docker) — manage the Compose containers from the sidebar
- **Thunder Client** (rangav.vscode-thunder-client) — test the FastAPI endpoints without leaving VS Code
- **YAML** (redhat.vscode-yaml) — editing `docker-compose.yml`
- Optional: **GitLens** (eamodio.gitlens) if you want richer Git history in VS Code

None of these are required to *run* the project — they make editing it easier.

---

## 2. Put this on GitHub

```bash
cd geoagentic-emergency-vehicle-support   # this folder
git init
git add .
git commit -m "Initial commit: GeoAgentic Emergency Vehicle Support prototype"
git branch -M main
git remote add origin https://github.com/<your-username>/<your-repo-name>.git
git push -u origin main
```

(Create the empty repo on github.com first — "New repository", don't
initialise it with a README, then use the URL it gives you above.)

`.gitignore` already excludes `node_modules/`, `.env`, `__pycache__/`, and
build output, so your API keys never get committed. **Never commit your real
`.env` file** — only the `.env.example` files are meant to be in Git.

---

## 3. Run it locally

### Step 1 — start the database (and, optionally, local OSRM)
```bash
docker compose up -d db
```
This starts PostgreSQL 16 with the PostGIS extension on port `5432`.

The `routing.py` service defaults to the free public OSRM demo server
(`https://router.project-osrm.org`) so you can run the whole demo with **zero
extra downloads**. If you want the "Local OSRM Engine" to actually be local
(closer to your architecture diagram), see `docs/ARCHITECTURE.md` §4 for how
to pull a small city's map extract and run `docker compose up -d osrm`
instead — this needs a one-time ~50–300 MB `.osm.pbf` download from
Geofabrik, so it's marked optional for the demo.

### Step 2 — backend
```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # then paste in your GEMINI_API_KEY
python -m app.seed_route        # loads the sample planned route into PostGIS
uvicorn app.main:socket_app --reload --port 8000
```
Backend is now on `http://localhost:8000` (Socket.IO on the same port).

### Step 3 — telemetry simulator (Simulation Layer, step 1)
In a new terminal:
```bash
cd simulation
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python telemetry_simulator.py
```
This streams a mock ambulance GPS point every 2 seconds and, partway through
the route, jumps off-path to simulate the "virtual roadblock" from your
scenario slide — this is what triggers steps 3–8.

### Step 4 — Laptop Admin Dashboard (Control Room Operator)
In a new terminal:
```bash
cd dashboard
npm install
cp .env.example .env            # paste in your VITE_MAPBOX_TOKEN
npm run dev
```
Open `http://localhost:5173`. You'll see the live ambulance marker, and when
a deviation is detected, the AI Decision Card (step 6) with
**Approve Reroute** / **Override** buttons.

### Step 5 — Mobile Driver PWA + Civilian view
In a new terminal:
```bash
cd driver-pwa
npm install
cp .env.example .env            # paste in your VITE_MAPBOX_TOKEN
npm run dev
```
Open `http://localhost:5174/?role=driver` on the ambulance driver's phone (or
another browser tab), and `http://localhost:5174/?role=civilian` on a second
phone/tab to see the geofenced yield warning arrive when the simulator's
vehicle comes within 500 m.

---

## 4. Deploying it (so it's not just `localhost`)

For a college demo, the easiest free path is:

| Piece | Where | Why |
|---|---|---|
| Backend (FastAPI + Socket.IO) | **Render** (free web service) or **Fly.io** | both support long-lived WebSocket connections, which Vercel/Netlify's serverless functions do not |
| PostgreSQL + PostGIS | **Neon** or **Supabase** (both have a free Postgres tier with PostGIS enabled) or Render's managed Postgres | no server to maintain |
| Dashboard (React) | **Vercel** or **Netlify** | `npm run build` → drag-and-drop the `dist/` folder, or connect the GitHub repo for auto-deploy |
| Driver PWA (React) | **Vercel** or **Netlify** | same as above; PWA installability needs HTTPS, which these give you free |
| OSRM | keep using the public demo server, or a small Docker container on Render | avoids hosting a large map file yourself |

Step-by-step for each is in `docs/ARCHITECTURE.md` §5.

---

## 5. Project layout
```
geoagentic-emergency-vehicle-support/
├── docker-compose.yml
├── backend/            FastAPI + Socket.IO + PostGIS + OSRM client + Gemini client
├── simulation/         Python Telemetry Script (Simulation Layer)
├── dashboard/          React + Mapbox GL — Laptop Admin Dashboard
├── driver-pwa/         React PWA — Mobile Driver + Civilian Driver views
└── docs/               Architecture notes, deployment walkthrough
```
