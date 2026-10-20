"""
Pramaan AI Backend - FastAPI Entry Point.
AI-Powered Training Centre Monitoring System with Live WebSockets & End-to-End AI Pipeline.
"""

from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.database import init_db, close_db, async_session
from app.core.websocket import ws_manager
from app.services.seed import seed_database_if_empty

from app.api import (
    centres_router,
    attendance_router,
    inventory_router,
    telemetry_router,
    discrepancy_router,
    dashboard_router,
    pipeline_router,
    edge_router,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager: sets up DB tables and seeds initial data."""
    print("[Lifespan] Starting up Pramaan AI Backend API...")
    await init_db()

    # Seed mock data if DB is empty
    data_path = Path(settings.DATA_PATH)
    async with async_session() as session:
        await seed_database_if_empty(session, data_path)

    yield

    print("[Lifespan] Shutting down Pramaan AI Backend API...")
    await close_db()


app = FastAPI(
    title="Pramaan AI API",
    description="AI-Powered Training Centre Monitoring - Discrepancy & Verification Engine with Live WebSockets",
    version="0.5.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static file serving for evidence and annotated frames
output_dir = Path(settings.OUTPUT_PATH)
output_dir.mkdir(parents=True, exist_ok=True)
app.mount("/output", StaticFiles(directory=str(output_dir)), name="output")

# Include API Routers under /api
app.include_router(centres_router, prefix="/api")
app.include_router(attendance_router, prefix="/api")
app.include_router(inventory_router, prefix="/api")
app.include_router(telemetry_router, prefix="/api")
app.include_router(discrepancy_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")
app.include_router(pipeline_router, prefix="/api")
app.include_router(edge_router, prefix="/api")


# WebSocket live updates channel
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            # Keep connection alive & listen for client ping
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception:
        ws_manager.disconnect(websocket)


@app.get("/")
async def root():
    return {
        "project": "Pramaan AI Monitoring API",
        "version": "0.5.0",
        "phase": "Phase 5 - End-to-End Pipeline & Real-Time Sync Complete",
        "websocket": "/ws",
        "documentation": "/docs",
        "endpoints": {
            "centres": "/api/centres",
            "attendance": "/api/attendance",
            "inventory": "/api/inventory",
            "telemetry": "/api/telemetry",
            "discrepancies": "/api/discrepancies",
            "pipeline": "/api/pipeline/process-video",
            "edge_simulation": "/api/edge/status",
            "dashboard_stats": "/api/dashboard/stats",
            "dashboard_map": "/api/dashboard/map",
        }
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "pramaan-ai-backend",
        "version": "0.5.0",
        "websocket_active_clients": len(ws_manager.active_connections)
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
