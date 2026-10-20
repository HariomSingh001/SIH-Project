"""
AI Telemetry Ingestion & Query Endpoints.
Receives lightweight edge telemetry payloads, stores detections, triggers discrepancy reconciliation,
and broadcasts live updates over WebSockets.
"""

import uuid
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..core.database import get_db
from ..core.websocket import ws_manager
from ..models.models import TelemetryRecord, Centre
from ..schemas.schemas import TelemetryPayload, TelemetryResponse
from ..services.discrepancy import reconcile_attendance_with_telemetry, evaluate_equipment_compliance

router = APIRouter(prefix="/telemetry", tags=["AI Telemetry"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def ingest_telemetry(
    payload: TelemetryPayload,
    db: AsyncSession = Depends(get_db)
):
    """
    Ingest a telemetry packet sent from the edge AI vision engine.
    Stores the telemetry, automatically runs discrepancy analysis, and broadcasts via WebSocket.
    """
    # Verify centre exists
    c_stmt = select(Centre).where(Centre.centre_id == payload.centre_id)
    centre = (await db.execute(c_stmt)).scalar_one_or_none()
    if not centre:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Centre '{payload.centre_id}' not found in registry."
        )

    tel_id = payload.telemetry_id or f"TEL-{payload.centre_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{str(uuid.uuid4())[:4]}"

    record = TelemetryRecord(
        telemetry_id=tel_id,
        centre_id=payload.centre_id,
        camera_id=payload.camera_id,
        camera_location=payload.camera_location,
        batch_id=payload.batch_id,
        timestamp=payload.timestamp,
        frame_index=payload.frame_index,
        total_detected_persons=payload.total_detected_persons,
        confidence_avg=payload.confidence_avg,
        roi_area=payload.roi_area,
        bounding_boxes=payload.bounding_boxes,
        equipment_detected=payload.equipment_detected,
        evidence_frame_path=payload.evidence_frame_path,
        privacy_masked=payload.privacy_masked,
    )
    db.add(record)
    await db.flush()

    # Reconcile attendance with telemetry
    att_alert = await reconcile_attendance_with_telemetry(
        session=db,
        centre_id=payload.centre_id,
        batch_id=payload.batch_id,
        detected_count=payload.total_detected_persons,
        timestamp_str=payload.timestamp,
        evidence_frame_path=payload.evidence_frame_path,
    )

    # Evaluate equipment if provided
    eq_alerts = []
    if payload.equipment_detected:
        eq_alerts = await evaluate_equipment_compliance(
            session=db,
            centre_id=payload.centre_id,
            detected_equipment=payload.equipment_detected,
            timestamp_str=payload.timestamp,
            evidence_frame_path=payload.evidence_frame_path,
        )

    await db.commit()

    all_alerts = []
    if att_alert:
        all_alerts.append({
            "alert_id": att_alert.alert_id,
            "centre_id": att_alert.centre_id,
            "severity": att_alert.severity,
            "alert_type": att_alert.alert_type,
            "description": att_alert.description,
            "claimed_value": att_alert.claimed_value,
            "detected_value": att_alert.detected_value,
            "percentage_gap": att_alert.percentage_gap
        })
    for a in eq_alerts:
        all_alerts.append({
            "alert_id": a.alert_id,
            "centre_id": a.centre_id,
            "severity": a.severity,
            "alert_type": a.alert_type,
            "description": a.description,
            "claimed_value": a.claimed_value,
            "detected_value": a.detected_value,
            "percentage_gap": a.percentage_gap
        })

    # Broadcast event via WebSocket
    await ws_manager.broadcast("TELEMETRY_INGESTED", {
        "telemetry_id": tel_id,
        "centre_id": payload.centre_id,
        "centre_name": centre.centre_name,
        "camera_id": payload.camera_id,
        "persons_detected": payload.total_detected_persons,
        "confidence_avg": payload.confidence_avg,
        "timestamp": payload.timestamp,
        "evidence_frame_path": payload.evidence_frame_path,
        "alerts_generated": len(all_alerts)
    })

    if all_alerts:
        await ws_manager.broadcast("NEW_DISCREPANCY_ALERT", {
            "centre_id": payload.centre_id,
            "centre_name": centre.centre_name,
            "alerts": all_alerts
        })

    return {
        "status": "success",
        "telemetry_id": tel_id,
        "centre_id": payload.centre_id,
        "persons_detected": payload.total_detected_persons,
        "discrepancy_checked": True,
        "alerts_generated": [a["alert_id"] for a in all_alerts],
        "message": f"Telemetry ingested successfully. Generated {len(all_alerts)} alert(s)."
    }


@router.post("/batch", status_code=status.HTTP_201_CREATED)
async def ingest_telemetry_batch(
    payloads: List[TelemetryPayload],
    db: AsyncSession = Depends(get_db)
):
    """
    Ingest a batch of telemetry packets from edge Store-and-Forward sync.
    Processes packets chronologically and broadcasts sync summary.
    """
    if not payloads:
        return {"status": "success", "count": 0, "alerts_generated": 0}

    total_ingested = 0
    total_alerts = 0

    for payload in payloads:
        tel_id = payload.telemetry_id or f"TEL-BATCH-{payload.centre_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{str(uuid.uuid4())[:4]}"
        record = TelemetryRecord(
            telemetry_id=tel_id,
            centre_id=payload.centre_id,
            camera_id=payload.camera_id,
            camera_location=payload.camera_location,
            batch_id=payload.batch_id,
            timestamp=payload.timestamp,
            frame_index=payload.frame_index,
            total_detected_persons=payload.total_detected_persons,
            confidence_avg=payload.confidence_avg,
            roi_area=payload.roi_area,
            bounding_boxes=payload.bounding_boxes,
            equipment_detected=payload.equipment_detected,
            evidence_frame_path=payload.evidence_frame_path,
            privacy_masked=payload.privacy_masked,
        )
        db.add(record)
        await db.flush()

        att_alert = await reconcile_attendance_with_telemetry(
            session=db,
            centre_id=payload.centre_id,
            batch_id=payload.batch_id,
            detected_count=payload.total_detected_persons,
            timestamp_str=payload.timestamp,
            evidence_frame_path=payload.evidence_frame_path,
        )
        if att_alert:
            total_alerts += 1
        total_ingested += 1

    await db.commit()

    # Broadcast batch sync completion
    await ws_manager.broadcast("STORE_AND_FORWARD_SYNCED", {
        "packets_synced": total_ingested,
        "new_alerts_detected": total_alerts,
        "timestamp": datetime.utcnow().isoformat()
    })

    return {
        "status": "success",
        "synced_packets": total_ingested,
        "new_alerts_detected": total_alerts,
        "message": f"Store-and-forward batch sync complete: {total_ingested} packets ingested, {total_alerts} alert(s) generated."
    }


@router.get("/latest", response_model=List[TelemetryResponse])
async def get_latest_telemetry(
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve the most recent telemetry packets received from edge cameras."""
    stmt = select(TelemetryRecord).order_by(TelemetryRecord.created_at.desc()).limit(limit)
    res = await db.execute(stmt)
    return res.scalars().all()


@router.get("/centre/{centre_id}", response_model=List[TelemetryResponse])
async def get_centre_telemetry(
    centre_id: str,
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve historical telemetry packets for a specific centre."""
    stmt = (
        select(TelemetryRecord)
        .where(TelemetryRecord.centre_id == centre_id)
        .order_by(TelemetryRecord.created_at.desc())
        .limit(limit)
    )
    res = await db.execute(stmt)
    return res.scalars().all()
