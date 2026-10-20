"""
Discrepancy Calculation Engine.
Compares claimed attendance and sanctioned inventory against AI telemetry.
Classifies severity (Normal, Warning, Critical) and creates discrepancy alerts.
"""

import uuid
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from ..models.models import AttendanceRecord, SanctionedEquipment, DiscrepancyAlert, Centre
from ..core.config import settings
from .scoring import recalculate_centre_trust_score


def evaluate_attendance_discrepancy(claimed: int, detected: int) -> Tuple[str, str, float, str]:
    """
    Evaluates attendance discrepancy between claimed student count and AI detected count.
    
    Returns:
        (severity, alert_type, percentage_gap, description)
    """
    if claimed <= 0:
        return "Normal", "ATTENDANCE_DEFICIT", 0.0, "Zero claimed attendance."

    diff = claimed - detected
    percentage_gap = (diff / claimed) * 100.0

    # Case 1: Ghost Batch (claimed attendance high, but AI detected 0 or <= 2)
    if claimed >= 10 and detected <= 1:
        severity = "Critical"
        alert_type = "GHOST_BATCH"
        description = f"Possible Ghost Batch detected: Claimed {claimed} students, but AI vision verified only {detected} present."
        return severity, alert_type, percentage_gap, description

    # Case 2: Surplus (detected > claimed - e.g. combined batches or visitors)
    if diff < 0:
        surplus_pct = (abs(diff) / claimed) * 100.0
        if surplus_pct > 30.0:
            severity = "Warning"
            alert_type = "UNSANCTIONED_OVERCROWDING"
            description = f"Overcrowding alert: AI detected {detected} persons, exceeding claimed {claimed} by {abs(diff)}."
        else:
            severity = "Normal"
            alert_type = "ATTENDANCE_SURPLUS"
            description = f"Normal attendance: AI detected {detected} (exceeds claimed {claimed} slightly)."
        return severity, alert_type, surplus_pct, description

    # Case 3: Attendance Deficit (claimed > detected)
    if percentage_gap <= settings.ACCEPTABLE_MARGIN_PERCENT:
        severity = "Normal"
        alert_type = "ATTENDANCE_MATCH"
        description = f"Verified: AI detected {detected} students (within acceptable margin of claimed {claimed})."
    elif percentage_gap < settings.DISCREPANCY_CRITICAL_PERCENT:
        severity = "Warning"
        alert_type = "ATTENDANCE_DEFICIT"
        description = f"Moderate attendance deficit: Claimed {claimed}, AI detected {detected} ({percentage_gap:.1f}% deficit)."
    else:
        severity = "Critical"
        alert_type = "ATTENDANCE_DEFICIT"
        description = f"Critical attendance deficit: Claimed {claimed}, AI detected {detected} ({percentage_gap:.1f}% deficit)."

    return severity, alert_type, percentage_gap, description


async def reconcile_attendance_with_telemetry(
    session: AsyncSession,
    centre_id: str,
    batch_id: Optional[str],
    detected_count: int,
    timestamp_str: str,
    evidence_frame_path: Optional[str] = None
) -> Optional[DiscrepancyAlert]:
    """
    Matches incoming telemetry with an attendance record for the centre and records discrepancy.
    """
    # Find matching attendance record (same centre & batch, or latest pending for this centre)
    stmt = select(AttendanceRecord).where(
        AttendanceRecord.centre_id == centre_id
    )
    if batch_id:
        stmt = stmt.where(AttendanceRecord.batch_id == batch_id)

    stmt = stmt.order_by(AttendanceRecord.submitted_at.desc()).limit(1)
    result = await session.execute(stmt)
    record = result.scalar_one_or_none()

    if not record:
        return None

    # Update attendance record with AI findings
    record.ai_detected_count = detected_count
    diff = record.claimed_attendance - detected_count
    record.discrepancy = diff

    severity, alert_type, gap, description = evaluate_attendance_discrepancy(
        record.claimed_attendance, detected_count
    )

    if severity == "Normal":
        record.verification_status = "Verified"
    else:
        record.verification_status = "Discrepancy"

    alert = None
    # If discrepancy is Warning or Critical, log an alert
    if severity in ["Warning", "Critical"]:
        alert_id = f"ALT-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{str(uuid.uuid4())[:6]}"
        alert = DiscrepancyAlert(
            alert_id=alert_id,
            centre_id=centre_id,
            batch_id=record.batch_id,
            record_id=record.record_id,
            timestamp=timestamp_str,
            alert_type=alert_type,
            severity=severity,
            claimed_value=float(record.claimed_attendance),
            detected_value=float(detected_count),
            difference=float(diff),
            percentage_gap=round(gap, 2),
            description=description,
            status="Open",
            evidence_frame_path=evidence_frame_path
        )
        session.add(alert)

    # Recalculate centre trust score and status
    await recalculate_centre_trust_score(session, centre_id)

    return alert


async def evaluate_equipment_compliance(
    session: AsyncSession,
    centre_id: str,
    detected_equipment: Dict[str, Any],
    timestamp_str: str,
    evidence_frame_path: Optional[str] = None
) -> list[DiscrepancyAlert]:
    """
    Compares AI detected equipment counts with sanctioned requirements.
    """
    stmt = select(SanctionedEquipment).where(
        SanctionedEquipment.centre_id == centre_id
    )
    result = await session.execute(stmt)
    items = result.scalars().all()

    created_alerts = []
    items_list = detected_equipment.get("items_detected", []) if isinstance(detected_equipment, dict) else []
    detected_map = {item.get("class", "").lower(): item.get("count", 0) for item in items_list if isinstance(item, dict)}

    # Mapping common detector classes to inventory names
    class_aliases = {
        "desktop_computer": ["computer", "desktop", "pc", "it equipment"],
        "monitor": ["lcd monitor", "screen", "display"],
        "chair": ["student chair", "chair"],
        "desk": ["student desk", "table"]
    }

    for eq in items:
        # Check if this item is tracked by the camera detection
        matched_count = None
        for det_class, count in detected_map.items():
            aliases = class_aliases.get(det_class, [det_class])
            if any(alias in eq.item_name.lower() for alias in aliases):
                matched_count = count
                break

        if matched_count is not None:
            eq.last_verified = timestamp_str[:10]
            eq.last_verified_count = matched_count

            if matched_count < eq.minimum_required:
                deficit = eq.minimum_required - matched_count
                pct = (deficit / eq.minimum_required) * 100.0
                severity = "Critical" if pct >= 30.0 else "Warning"

                alert_id = f"ALT-EQ-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{str(uuid.uuid4())[:6]}"
                alert = DiscrepancyAlert(
                    alert_id=alert_id,
                    centre_id=centre_id,
                    batch_id=None,
                    record_id=eq.item_id,
                    timestamp=timestamp_str,
                    alert_type="EQUIPMENT_DEFICIT",
                    severity=severity,
                    claimed_value=float(eq.minimum_required),
                    detected_value=float(matched_count),
                    difference=float(deficit),
                    percentage_gap=round(pct, 2),
                    description=f"Equipment deficit: {eq.item_name} minimum required is {eq.minimum_required}, but only {matched_count} detected.",
                    status="Open",
                    evidence_frame_path=evidence_frame_path
                )
                session.add(alert)
                created_alerts.append(alert)

    if created_alerts:
        await recalculate_centre_trust_score(session, centre_id)

    return created_alerts
