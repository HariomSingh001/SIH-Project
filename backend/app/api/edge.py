"""
Edge Simulation & Store-and-Forward API Endpoints.
Allows dashboard users to simulate network outages, offline edge buffering, and batch synchronization.
"""

import random
from datetime import datetime
from fastapi import APIRouter, status
from pydantic import BaseModel
from ai_engine.edge.store_and_forward import EdgeStoreAndForwardManager

router = APIRouter(prefix="/edge", tags=["Edge & Store-and-Forward"])

# Edge manager instance
edge_manager = EdgeStoreAndForwardManager()


class NetworkStatusToggle(BaseModel):
    is_online: bool


@router.get("/status")
async def get_edge_status():
    """Retrieve edge agent connectivity status and buffer queue statistics."""
    return {
        "is_online": edge_manager.is_online,
        "buffered_packets_count": edge_manager.get_buffered_count(),
        "buffered_size_bytes": edge_manager.get_buffered_size_bytes(),
        "storage_mode": "Encrypted Local SQLite Buffer (Simulated)",
        "network_label": "🟢 Online (Direct Sync)" if edge_manager.is_online else "🔴 Offline (Local Buffering)"
    }


@router.post("/toggle-network")
async def toggle_edge_network(payload: NetworkStatusToggle):
    """Toggle simulated edge network connectivity (Online / Offline)."""
    edge_manager.set_network_status(payload.is_online)
    return {
        "status": "success",
        "is_online": edge_manager.is_online,
        "buffered_count": edge_manager.get_buffered_count(),
        "message": f"Edge network status set to: {'ONLINE' if edge_manager.is_online else 'OFFLINE'}"
    }


@router.post("/generate-sample-packet")
async def generate_edge_packet():
    """
    Simulates edge camera vision detection generating a new telemetry frame.
    If network is online -> transmits directly.
    If network is offline -> buffers locally.
    """
    now = datetime.utcnow().isoformat()
    # Realistic student count with potential discrepancy
    detected_count = random.choice([14, 16, 18, 20, 24])

    sample_packet = {
        "centre_id": "CTR-DL-001",
        "camera_id": "CAM-DL001-01",
        "camera_location": "Classroom 1",
        "batch_id": "BTH-DL001-A",
        "timestamp": now,
        "frame_index": random.randint(10, 300),
        "total_detected_persons": detected_count,
        "confidence_avg": round(random.uniform(0.85, 0.94), 2),
        "roi_area": "classroom_seating",
        "equipment_detected": {
            "items_detected": [
                {"class": "desktop_computer", "count": 28, "confidence_avg": 0.92},
                {"class": "chair", "count": 32, "confidence_avg": 0.89}
            ]
        },
        "evidence_frame_path": "/output/evidence/2026-10-20_02-54-07_blurred.jpg",
        "privacy_masked": True
    }

    result = await edge_manager.ingest_packet(sample_packet)
    result["is_online"] = edge_manager.is_online
    result["buffered_packets_count"] = edge_manager.get_buffered_count()
    return result


@router.post("/flush")
async def flush_edge_buffer():
    """Synchronize all locally buffered packets to the central database."""
    if not edge_manager.is_online:
        return {
            "status": "error",
            "message": "Cannot sync while network is offline! Please restore network connectivity first."
        }

    result = await edge_manager.flush_buffer()
    result["buffered_packets_count"] = edge_manager.get_buffered_count()
    return result
