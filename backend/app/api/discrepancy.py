"""
Discrepancy Alert & Verification Endpoints.
Allows monitoring teams to view, filter, acknowledge, and resolve discrepancy alerts.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from ..core.database import get_db
from ..models.models import DiscrepancyAlert, Centre, AttendanceRecord
from ..schemas.schemas import (
    DiscrepancyAlertResponse,
    DiscrepancyAlertUpdate,
)
from ..services.scoring import recalculate_centre_trust_score

router = APIRouter(prefix="/discrepancies", tags=["Discrepancies"])


@router.get("", response_model=List[DiscrepancyAlertResponse])
async def list_discrepancies(
    centre_id: Optional[str] = Query(None, description="Filter by Centre ID"),
    severity: Optional[str] = Query(None, description="Filter by Severity (Normal, Warning, Critical)"),
    status: Optional[str] = Query(None, description="Filter by Alert Status (Open, Acknowledged, Resolved, Escalated)"),
    alert_type: Optional[str] = Query(None, description="Filter by Alert Type (ATTENDANCE_DEFICIT, GHOST_BATCH, EQUIPMENT_DEFICIT)"),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve discrepancy alerts with multi-criteria filtering."""
    stmt = (
        select(DiscrepancyAlert, Centre.centre_name)
        .outerjoin(Centre, DiscrepancyAlert.centre_id == Centre.centre_id)
    )

    if centre_id:
        stmt = stmt.where(DiscrepancyAlert.centre_id == centre_id)
    if severity:
        stmt = stmt.where(DiscrepancyAlert.severity == severity)
    if status:
        stmt = stmt.where(DiscrepancyAlert.status == status)
    if alert_type:
        stmt = stmt.where(DiscrepancyAlert.alert_type == alert_type)

    stmt = stmt.order_by(DiscrepancyAlert.created_at.desc()).limit(limit)
    res = await db.execute(stmt)

    alerts = []
    for alert, centre_name in res.all():
        resp_item = DiscrepancyAlertResponse.model_validate(alert)
        resp_item.centre_name = centre_name
        alerts.append(resp_item)

    return alerts


@router.get("/{alert_id}", response_model=DiscrepancyAlertResponse)
async def get_discrepancy(
    alert_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Retrieve a single discrepancy alert by ID."""
    stmt = (
        select(DiscrepancyAlert, Centre.centre_name)
        .outerjoin(Centre, DiscrepancyAlert.centre_id == Centre.centre_id)
        .where(DiscrepancyAlert.alert_id == alert_id)
    )
    res = await db.execute(stmt)
    row = res.first()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Discrepancy alert '{alert_id}' not found."
        )

    alert, centre_name = row
    resp_item = DiscrepancyAlertResponse.model_validate(alert)
    resp_item.centre_name = centre_name
    return resp_item


@router.patch("/{alert_id}/status", response_model=DiscrepancyAlertResponse)
async def update_alert_status(
    alert_id: str,
    payload: DiscrepancyAlertUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update status of a discrepancy alert (Open, Acknowledged, Resolved, Escalated)."""
    valid_statuses = ["Open", "Acknowledged", "Resolved", "Escalated"]
    if payload.status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status '{payload.status}'. Must be one of: {valid_statuses}"
        )

    stmt = select(DiscrepancyAlert).where(DiscrepancyAlert.alert_id == alert_id)
    res = await db.execute(stmt)
    alert = res.scalar_one_or_none()
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Discrepancy alert '{alert_id}' not found."
        )

    alert.status = payload.status
    await db.flush()

    # Recalculate centre trust score since open alerts changed
    await recalculate_centre_trust_score(db, alert.centre_id)
    await db.commit()
    await db.refresh(alert)

    # Fetch centre name
    c_stmt = select(Centre.centre_name).where(Centre.centre_id == alert.centre_id)
    c_name = (await db.execute(c_stmt)).scalar_one_or_none()

    resp_item = DiscrepancyAlertResponse.model_validate(alert)
    resp_item.centre_name = c_name
    return resp_item
