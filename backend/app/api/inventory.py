"""
Sanctioned Equipment Inventory Endpoints.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..core.database import get_db
from ..models.models import SanctionedEquipment
from ..schemas.schemas import EquipmentResponse, EquipmentUpdate

router = APIRouter(prefix="/inventory", tags=["Inventory"])


@router.get("", response_model=List[EquipmentResponse])
async def list_equipment(
    centre_id: Optional[str] = Query(None, description="Filter by Centre ID"),
    category: Optional[str] = Query(None, description="Filter by Category"),
    status: Optional[str] = Query(None, description="Filter by Status (Mandatory, Optional)"),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve equipment inventory with optional filtering."""
    stmt = select(SanctionedEquipment)
    if centre_id:
        stmt = stmt.where(SanctionedEquipment.centre_id == centre_id)
    if category:
        stmt = stmt.where(SanctionedEquipment.category == category)
    if status:
        stmt = stmt.where(SanctionedEquipment.status == status)

    stmt = stmt.order_by(SanctionedEquipment.centre_id.asc(), SanctionedEquipment.item_id.asc())
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/centre/{centre_id}", response_model=List[EquipmentResponse])
async def get_centre_inventory(
    centre_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get all sanctioned equipment for a specific centre."""
    stmt = select(SanctionedEquipment).where(SanctionedEquipment.centre_id == centre_id)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.put("/{item_id}", response_model=EquipmentResponse)
async def update_equipment_verification(
    item_id: str,
    payload: EquipmentUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update verified count and audit notes for an equipment item."""
    stmt = select(SanctionedEquipment).where(SanctionedEquipment.item_id == item_id)
    item = (await db.execute(stmt)).scalar_one_or_none()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Equipment item '{item_id}' not found."
        )

    update_data = payload.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(item, field, val)

    await db.commit()
    await db.refresh(item)
    return item
