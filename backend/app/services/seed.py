"""
Database Seeding Service.
Seeds initial mock data from data/ directory into the database if tables are empty.
"""

import json
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from ..models.models import (
    Centre,
    Batch,
    Camera,
    AttendanceRecord,
    SanctionedEquipment,
    TelemetryRecord,
    DiscrepancyAlert,
)
from .discrepancy import evaluate_attendance_discrepancy
from .scoring import recalculate_centre_trust_score


async def seed_database_if_empty(session: AsyncSession, data_dir: Path):
    """
    Checks if database already contains centres. If empty, reads JSON files from data_dir
    and populates tables.
    """
    res = await session.execute(select(func.count(Centre.centre_id)))
    count = res.scalar() or 0

    if count > 0:
        print(f"[Seed] Database already contains {count} centres. Skipping seeding.")
        return

    print("[Seed] Database is empty. Seeding mock data from:", data_dir)

    # 1. Seed Centres, Batches, Cameras
    centres_file = data_dir / "centres" / "centres.json"
    if centres_file.exists():
        with open(centres_file, "r", encoding="utf-8") as f:
            centres_data = json.load(f)

        for c in centres_data:
            centre = Centre(
                centre_id=c["centre_id"],
                centre_name=c["centre_name"],
                state=c["state"],
                city=c["city"],
                district=c.get("district", c["city"]),
                address=c["address"],
                latitude=c["latitude"],
                longitude=c["longitude"],
                centre_type=c.get("centre_type", "PMKVY"),
                empanelment_status=c.get("empanelment_status", "Active"),
                total_capacity=c.get("total_capacity", 0),
                active_batches=c.get("active_batches", 0),
                sector=c.get("sector", "General"),
                connectivity=c.get("connectivity"),
                contact_person=c.get("contact_person"),
                contact_phone=c.get("contact_phone"),
                trust_score=c.get("trust_score", 100.0),
                last_physical_audit=c.get("last_physical_audit"),
                compliance_status=c.get("compliance_status", "Normal"),
            )
            session.add(centre)

            # Batches / Courses
            for course in c.get("courses", []):
                batch = Batch(
                    batch_id=course["batch_id"],
                    centre_id=c["centre_id"],
                    course_id=course["course_id"],
                    course_name=course["course_name"],
                    batch_size=course.get("batch_size", 30),
                    start_date=course.get("start_date", "2026-09-01"),
                    end_date=course.get("end_date", "2026-12-01"),
                    shift=course.get("shift", "Morning"),
                )
                session.add(batch)

            # Cameras
            for cam in c.get("cameras", []):
                camera = Camera(
                    camera_id=cam["camera_id"],
                    centre_id=c["centre_id"],
                    location=cam.get("location", "Classroom"),
                    type=cam.get("type", "Indoor"),
                    resolution=cam.get("resolution", "1080p"),
                    status="Active",
                )
                session.add(camera)

        await session.flush()
        print(f"[Seed] Seeded {len(centres_data)} centres with batches and cameras.")

    # 2. Seed Sanctioned Equipment
    inventory_file = data_dir / "inventory" / "sanctioned_equipment.json"
    if inventory_file.exists():
        with open(inventory_file, "r", encoding="utf-8") as f:
            inv_data = json.load(f)

        eq_count = 0
        for centre_inv in inv_data:
            c_id = centre_inv["centre_id"]
            for item in centre_inv.get("equipment", []):
                eq = SanctionedEquipment(
                    item_id=item["item_id"],
                    centre_id=c_id,
                    item_name=item["item_name"],
                    category=item.get("category", "General"),
                    sanctioned_count=item.get("sanctioned_count", 0),
                    minimum_required=item.get("minimum_required", 0),
                    location=item.get("location", "Classroom"),
                    status=item.get("status", "Mandatory"),
                    last_verified=item.get("last_verified"),
                    last_verified_count=item.get("last_verified_count"),
                    notes=item.get("notes", ""),
                )
                session.add(eq)
                eq_count += 1

        await session.flush()
        print(f"[Seed] Seeded {eq_count} equipment items.")

    # 3. Seed Attendance Records
    attendance_dir = data_dir / "attendance"
    att_count = 0
    if attendance_dir.exists():
        for att_file in sorted(attendance_dir.glob("*.json")):
            with open(att_file, "r", encoding="utf-8") as f:
                records = json.load(f)

            for r in records:
                # Check if already seeded
                record = AttendanceRecord(
                    record_id=r["record_id"],
                    centre_id=r["centre_id"],
                    batch_id=r["batch_id"],
                    course_name=r["course_name"],
                    date=r["date"],
                    shift=r["shift"],
                    claimed_attendance=r["claimed_attendance"],
                    batch_capacity=r.get("batch_capacity", 30),
                    attendance_percentage=r.get("attendance_percentage", 0.0),
                    submitted_by=r["submitted_by"],
                    submitted_at=r["submitted_at"],
                    ai_detected_count=r.get("ai_detected_count"),
                    discrepancy=r.get("discrepancy"),
                    verification_status=r.get("verification_status", "Pending"),
                    notes=r.get("notes", ""),
                )
                session.add(record)
                att_count += 1

        await session.flush()
        print(f"[Seed] Seeded {att_count} attendance records.")

    # 4. Seed Sample Telemetry & Generated Discrepancies
    telemetry_file = data_dir / "telemetry" / "sample_telemetry.json"
    if telemetry_file.exists():
        with open(telemetry_file, "r", encoding="utf-8") as f:
            tel_data = json.load(f)

        tel_count = 0
        for t in tel_data:
            p_det = t.get("person_detection", {})
            total_detected = p_det.get("total_detected", 0)

            record = TelemetryRecord(
                telemetry_id=t.get("telemetry_id", f"TEL-{t['centre_id']}-{t['frame_index']}"),
                centre_id=t["centre_id"],
                camera_id=t.get("camera_id", "CAM-01"),
                camera_location=t.get("camera_location", "Classroom"),
                batch_id=t.get("batch_id"),
                timestamp=t["timestamp"],
                frame_index=t.get("frame_index", 0),
                total_detected_persons=total_detected,
                confidence_avg=p_det.get("confidence_avg", 0.85),
                roi_area=p_det.get("roi_area", "classroom_seating"),
                bounding_boxes=p_det.get("bounding_boxes", []),
                equipment_detected=t.get("equipment_detection", {}),
                evidence_frame_path=t.get("evidence_frame", "output/evidence/2026-10-20_02-54-07_blurred.jpg"),
                privacy_masked=True,
            )
            session.add(record)
            tel_count += 1

        await session.flush()
        print(f"[Seed] Seeded {tel_count} telemetry records.")

    # 5. Generate seed discrepancies for demonstration (matching mock attendance vs telemetry)
    # Check attendance records and create realistic alerts for demo centres
    stmt = select(AttendanceRecord).where(AttendanceRecord.centre_id.in_(["CTR-DL-001", "CTR-RJ-002", "CTR-WB-004"]))
    res = await session.execute(stmt)
    records = res.scalars().all()

    alert_idx = 1
    for r in records:
        # Simulate AI detection discrepancy for testing the dashboard
        if r.centre_id == "CTR-DL-001" and r.batch_id == "BTH-DL001-A":
            r.ai_detected_count = 18  # Claimed was 28
            r.discrepancy = 10
            r.verification_status = "Discrepancy"
            alert = DiscrepancyAlert(
                alert_id=f"ALT-INIT-{alert_idx:03d}",
                centre_id=r.centre_id,
                batch_id=r.batch_id,
                record_id=r.record_id,
                timestamp=r.submitted_at,
                alert_type="ATTENDANCE_DEFICIT",
                severity="Critical",
                claimed_value=float(r.claimed_attendance),
                detected_value=18.0,
                difference=10.0,
                percentage_gap=35.7,
                description=f"Critical attendance deficit: Claimed {r.claimed_attendance}, AI verified only 18 students present (35.7% deficit).",
                status="Open",
                evidence_frame_path="output/evidence/2026-10-20_02-54-07_blurred.jpg"
            )
            session.add(alert)
            alert_idx += 1

        elif r.centre_id == "CTR-RJ-002" and r.batch_id == "BTH-RJ002-A":
            r.ai_detected_count = 0  # Claimed 22, Detected 0 -> Ghost Batch
            r.discrepancy = 22
            r.verification_status = "Discrepancy"
            alert = DiscrepancyAlert(
                alert_id=f"ALT-INIT-{alert_idx:03d}",
                centre_id=r.centre_id,
                batch_id=r.batch_id,
                record_id=r.record_id,
                timestamp=r.submitted_at,
                alert_type="GHOST_BATCH",
                severity="Critical",
                claimed_value=float(r.claimed_attendance),
                detected_value=0.0,
                difference=22.0,
                percentage_gap=100.0,
                description=f"Ghost Batch Alert: Centre claimed full batch attendance ({r.claimed_attendance}), but zero students were detected during scheduled hours.",
                status="Open",
                evidence_frame_path="output/evidence/2026-10-20_02-54-07_blurred.jpg"
            )
            session.add(alert)
            alert_idx += 1

        elif r.centre_id == "CTR-WB-004":
            r.ai_detected_count = 20  # Claimed 25, Deficit of 5 (20%) -> Warning
            r.discrepancy = 5
            r.verification_status = "Discrepancy"
            alert = DiscrepancyAlert(
                alert_id=f"ALT-INIT-{alert_idx:03d}",
                centre_id=r.centre_id,
                batch_id=r.batch_id,
                record_id=r.record_id,
                timestamp=r.submitted_at,
                alert_type="ATTENDANCE_DEFICIT",
                severity="Warning",
                claimed_value=float(r.claimed_attendance),
                detected_value=20.0,
                difference=5.0,
                percentage_gap=20.0,
                description=f"Moderate attendance deficit: Claimed {r.claimed_attendance}, AI verified 20 students (20% deficit).",
                status="Acknowledged",
                evidence_frame_path="output/evidence/2026-10-20_02-54-07_blurred.jpg"
            )
            session.add(alert)
            alert_idx += 1

    await session.commit()
    print("[Seed] Initial mock data and discrepancy demo alerts committed.")
