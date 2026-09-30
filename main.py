from contextlib import asynccontextmanager

import socketio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine, Base, init_postgis
from app.sockets import sio
from app.routers import vehicles, alerts, decisions


@asynccontextmanager
async def lifespan(app: FastAPI):
    with engine.begin() as conn:
        init_postgis(conn)
        Base.metadata.create_all(bind=conn)
    yield


app = FastAPI(title="GeoAgentic Emergency Vehicle Support", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(vehicles.router)
app.include_router(alerts.router)
app.include_router(decisions.router)


@app.get("/health")
def health():
    return {"status": "ok"}


# Socket.IO wraps the FastAPI app - this combined ASGI app is what uvicorn runs.
socket_app = socketio.ASGIApp(sio, other_asgi_app=app)
