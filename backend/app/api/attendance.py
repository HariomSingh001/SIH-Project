"""
Attendance Record Endpoints.
Handles claimed attendance records, status lookups, and manual submissions.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..core.database import get_db
from ..models.models import AttendanceRecord
from ..schemas.schemas import AttendanceResponse, AttendanceCreate

router = APIRouter(prefix="/attendance", tags=["Attendance"])


@router.get("", response_model=List[AttendanceResponse])
async def list_attendance(
    centre_id: Optional[str] = Query(None, description="Filter by Centre ID"),
    date: Optional[str] = Query(None, description="Filter by Date (YYYY-MM-DD)"),
    status: Optional[str] = Query(None, description="Filter by Verification Status (Verified, Discrepancy, Pending)"),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve attendance records with optional filtering."""
    stmt = select(AttendanceRecord)
    if centre_id:
        stmt = stmt.where(AttendanceRecord.centre_id == centre_id)
    if date:
        stmt = stmt.where(AttendanceRecord.date == date)
    if status:
        stmt = stmt.where(AttendanceRecord.verification_status == status)

    stmt = stmt.order_by(AttendanceRecord.submitted_at.desc()).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/{record_id}", response_model=AttendanceResponse)
async def get_attendance_record(
    record_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific attendance record by ID."""
    stmt = select(AttendanceRecord).where(AttendanceRecord.record_id == record_id)
    record = (await db.execute(stmt)).scalar_one_or_none()
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Attendance record '{record_id}' not found."
        )
    return record


@router.post("", response_model=AttendanceResponse, status_code=status.HTTP_201_CREATED)
async def submit_attendance(
    payload: AttendanceCreate,
    db: AsyncSession = Depends(get_db)
):
    """Submit a daily attendance claim."""
    stmt = select(AttendanceRecord).where(AttendanceRecord.record_id == payload.record_id)
    existing = (await db.execute(stmt)).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Attendance record '{payload.record_id}' already exists."
        )

    record = AttendanceRecord(
        record_id=payload.record_id,
        centre_id=payload.centre_id,
        batch_id=payload.batch_id,
        course_name=payload.course_name,
        date=payload.date,
        shift=payload.shift,
        claimed_attendance=payload.claimed_attendance,
        batch_capacity=payload.batch_capacity,
        attendance_percentage=payload.attendance_percentage,
        submitted_by=payload.submitted_by,
        submitted_at=payload.submitted_at,
        ai_detected_count=payload.ai_detected_count,
        discrepancy=payload.discrepancy,
        verification_status=payload.verification_status,
        notes=payload.notes,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record
