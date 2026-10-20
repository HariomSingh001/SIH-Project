"""
Training Centre CRUD Endpoints.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from ..core.database import get_db
from ..models.models import Centre, Batch, Camera
from ..schemas.schemas import (
    CentreResponse,
    CentreDetailResponse,
    CentreCreate,
    CentreUpdate,
)

router = APIRouter(prefix="/centres", tags=["Centres"])


@router.get("", response_model=List[CentreResponse])
async def list_centres(
    state: Optional[str] = Query(None, description="Filter by state"),
    compliance_status: Optional[str] = Query(None, description="Filter by compliance status (Normal, Warning, Critical)"),
    db: AsyncSession = Depends(get_db)
):
    """List all training centres with optional filtering."""
    stmt = select(Centre)
    if state:
        stmt = stmt.where(Centre.state == state)
    if compliance_status:
        stmt = stmt.where(Centre.compliance_status == compliance_status)
    stmt = stmt.order_by(Centre.centre_id.asc())

    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/{centre_id}", response_model=CentreDetailResponse)
async def get_centre(
    centre_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Retrieve detailed information about a training centre including batches and cameras."""
    stmt = (
        select(Centre)
        .options(selectinload(Centre.batches), selectinload(Centre.cameras))
        .where(Centre.centre_id == centre_id)
    )
    result = await db.execute(stmt)
    centre = result.scalar_one_or_none()

    if not centre:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Centre with ID '{centre_id}' not found."
        )
    return centre


@router.post("", response_model=CentreResponse, status_code=status.HTTP_201_CREATED)
async def create_centre(
    payload: CentreCreate,
    db: AsyncSession = Depends(get_db)
):
    """Register a new training centre with courses and cameras."""
    stmt = select(Centre).where(Centre.centre_id == payload.centre_id)
    existing = (await db.execute(stmt)).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Centre with ID '{payload.centre_id}' already exists."
        )

    centre = Centre(
        centre_id=payload.centre_id,
        centre_name=payload.centre_name,
        state=payload.state,
        city=payload.city,
        district=payload.district,
        address=payload.address,
        latitude=payload.latitude,
        longitude=payload.longitude,
        centre_type=payload.centre_type,
        empanelment_status=payload.empanelment_status,
        total_capacity=payload.total_capacity,
        active_batches=payload.active_batches,
        sector=payload.sector,
        connectivity=payload.connectivity,
        contact_person=payload.contact_person,
        contact_phone=payload.contact_phone,
        trust_score=payload.trust_score,
        last_physical_audit=payload.last_physical_audit,
        compliance_status=payload.compliance_status,
    )
    db.add(centre)

    if payload.courses:
        for course in payload.courses:
            batch = Batch(
                batch_id=course.batch_id,
                centre_id=centre.centre_id,
                course_id=course.course_id,
                course_name=course.course_name,
                batch_size=course.batch_size,
                start_date=course.start_date,
                end_date=course.end_date,
                shift=course.shift,
            )
            db.add(batch)

    if payload.cameras:
        for cam in payload.cameras:
            camera = Camera(
                camera_id=cam.camera_id,
                centre_id=centre.centre_id,
                location=cam.location,
                type=cam.type,
                resolution=cam.resolution,
                status=cam.status,
            )
            db.add(camera)

    await db.commit()
    await db.refresh(centre)
    return centre


@router.put("/{centre_id}", response_model=CentreResponse)
async def update_centre(
    centre_id: str,
    payload: CentreUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update training centre information."""
    stmt = select(Centre).where(Centre.centre_id == centre_id)
    centre = (await db.execute(stmt)).scalar_one_or_none()
    if not centre:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Centre with ID '{centre_id}' not found."
        )

    update_data = payload.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(centre, field, val)

    await db.commit()
    await db.refresh(centre)
    return centre
