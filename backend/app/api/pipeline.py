"""
End-to-End Pipeline API Endpoint.
Processes video files through the AI Vision pipeline (Sampler -> YOLOv8 -> Face Blur -> Telemetry)
and pushes live WebSocket progress updates to the dashboard.
"""

import sys
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import settings
from ..core.database import get_db, async_session
from ..core.websocket import ws_manager
from ..models.models import TelemetryRecord, Centre
from ..services.discrepancy import reconcile_attendance_with_telemetry

# Add project root to sys.path so we can import ai_engine
project_root = Path(settings.PROJECT_ROOT)
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

router = APIRouter(prefix="/pipeline", tags=["Pipeline & AI Engine"])


class VideoProcessRequest(BaseModel):
    video_path: Optional[str] = "data/videos/15861386_1080_1920_30fps.mp4"
    centre_id: str = "CTR-DL-001"
    camera_id: str = "CAM-DL001-01"
    batch_id: Optional[str] = "BTH-DL001-A"
    sampling_interval: float = 2.0
    confidence: float = 0.25


async def run_pipeline_worker(params: VideoProcessRequest):
    """
    Background worker that runs the computer vision pipeline on a video file
    and streams progress events over WebSocket.
    """
    try:
        from ai_engine.main import PramaanAIPipeline

        video_full_path = project_root / params.video_path
        if not video_full_path.exists():
            await ws_manager.broadcast("PIPELINE_ERROR", {
                "error": f"Video file not found at: {params.video_path}"
            })
            return

        await ws_manager.broadcast("PIPELINE_STARTED", {
            "centre_id": params.centre_id,
            "camera_id": params.camera_id,
            "video_path": params.video_path,
            "status": "Initializing YOLOv8s Model and Frame Sampler..."
        })

        output_dir = project_root / "output"
        pipeline = PramaanAIPipeline(
            person_confidence=params.confidence,
            output_dir=str(output_dir)
        )

        # Run pipeline in a separate thread to avoid blocking asyncio event loop
        loop = asyncio.get_event_loop()
        telemetry_report = await loop.run_in_executor(
            None,
            pipeline.process_video,
            str(video_full_path),
            params.sampling_interval,
            params.centre_id,
            params.camera_id
        )

        frames_data = telemetry_report.get("frames", [])
        total_frames = len(frames_data)

        # Ingest frames into database and broadcast progress
        alerts_created = []
        async with async_session() as session:
            for idx, frame in enumerate(frames_data):
                p_det = frame.get("person_detection", {})
                persons_count = p_det.get("total_detected", 0)

                tel_id = f"TEL-LIVE-{params.centre_id}-{frame.get('frame_index', idx)}"
                rel_blurred_path = frame.get("evidence_frame", "")
                if "output" in rel_blurred_path:
                    # Make relative for frontend /output/...
                    idx_sub = rel_blurred_path.find("output")
                    rel_blurred_path = rel_blurred_path[idx_sub:].replace("\\", "/")

                record = TelemetryRecord(
                    telemetry_id=tel_id,
                    centre_id=params.centre_id,
                    camera_id=params.camera_id,
                    camera_location="Classroom 1",
                    batch_id=params.batch_id,
                    timestamp=frame.get("timestamp", datetime.utcnow().isoformat()),
                    frame_index=frame.get("frame_index", idx),
                    total_detected_persons=persons_count,
                    confidence_avg=p_det.get("confidence_avg", 0.85),
                    roi_area=p_det.get("roi_area", "classroom_seating"),
                    bounding_boxes=p_det.get("bounding_boxes", []),
                    evidence_frame_path=rel_blurred_path,
                    privacy_masked=True
                )
                session.add(record)

                # Reconcile with attendance
                alert = await reconcile_attendance_with_telemetry(
                    session=session,
                    centre_id=params.centre_id,
                    batch_id=params.batch_id,
                    detected_count=persons_count,
                    timestamp_str=frame.get("timestamp", datetime.utcnow().isoformat()),
                    evidence_frame_path=rel_blurred_path
                )
                if alert:
                    alerts_created.append(alert.alert_id)

                # Broadcast incremental progress event
                progress_pct = int(((idx + 1) / total_frames) * 100)
                await ws_manager.broadcast("PIPELINE_FRAME_PROCESSED", {
                    "frame_index": frame.get("frame_index", idx),
                    "total_frames": total_frames,
                    "progress_percent": progress_pct,
                    "persons_detected": persons_count,
                    "evidence_frame_path": rel_blurred_path,
                    "timestamp": frame.get("timestamp")
                })

            await session.commit()

        # Broadcast completion
        summary = telemetry_report.get("summary", {})
        bandwidth = telemetry_report.get("bandwidth_savings", {})

        await ws_manager.broadcast("PIPELINE_COMPLETE", {
            "centre_id": params.centre_id,
            "total_frames_processed": total_frames,
            "avg_persons_detected": summary.get("avg_persons_detected", 0),
            "max_persons_detected": summary.get("max_persons_detected", 0),
            "bandwidth_saving_pct": bandwidth.get("bandwidth_saving_percent", 97.3),
            "alerts_generated": len(alerts_created),
            "message": f"Pipeline analysis finished: {total_frames} frames processed. Generated {len(alerts_created)} alert(s)."
        })

    except Exception as e:
        print(f"[Pipeline Worker Error]: {e}")
        await ws_manager.broadcast("PIPELINE_ERROR", {
            "error": str(e)
        })


@router.post("/process-video", status_code=status.HTTP_202_ACCEPTED)
async def process_video(
    request: VideoProcessRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Trigger end-to-end AI vision analysis on a video file.
    Runs asynchronously and streams frame-by-frame progress over WebSocket.
    """
    # Verify centre exists
    stmt = select(Centre).where(Centre.centre_id == request.centre_id)
    centre = (await db.execute(stmt)).scalar_one_or_none()
    if not centre:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Centre '{request.centre_id}' not found."
        )

    # Launch background task
    background_tasks.add_task(run_pipeline_worker, request)

    return {
        "status": "processing_started",
        "centre_id": request.centre_id,
        "video": request.video_path,
        "websocket_channel": "/ws",
        "message": "AI Vision pipeline execution has been launched in background. Monitoring progress over WebSocket."
    }
