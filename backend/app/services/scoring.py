"""
Anomaly & Trust Scoring Service.
Maintains and dynamically computes centre trust scores (0-100) and compliance states.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from ..models.models import Centre, DiscrepancyAlert, AttendanceRecord


async def recalculate_centre_trust_score(session: AsyncSession, centre_id: str) -> float:
    """
    Recalculates a centre's trust score based on:
    - Base score = 100
    - Deduction for active Critical alerts: -15 pts each
    - Deduction for active Warning alerts: -5 pts each
    - Historical attendance discrepancy penalties
    - Score bounded between 0 and 100
    """
    stmt = select(Centre).where(Centre.centre_id == centre_id)
    res = await session.execute(stmt)
    centre = res.scalar_one_or_none()

    if not centre:
        return 100.0

    # Count open/acknowledged alerts
    alerts_stmt = select(DiscrepancyAlert).where(
        and_(
            DiscrepancyAlert.centre_id == centre_id,
            DiscrepancyAlert.status.in_(["Open", "Acknowledged"])
        )
    )
    alerts_res = await session.execute(alerts_stmt)
    alerts = alerts_res.scalars().all()

    critical_count = sum(1 for a in alerts if a.severity == "Critical")
    warning_count = sum(1 for a in alerts if a.severity == "Warning")

    # Historical attendance penalty: average discrepancy percentage
    att_stmt = select(AttendanceRecord).where(
        and_(
            AttendanceRecord.centre_id == centre_id,
            AttendanceRecord.verification_status == "Discrepancy"
        )
    )
    att_res = await session.execute(att_stmt)
    discrepant_att = att_res.scalars().all()
    unverified_penalty = min(len(discrepant_att) * 3.0, 25.0)

    # Base formula
    score = 100.0 - (critical_count * 15.0) - (warning_count * 5.0) - unverified_penalty
    score = max(5.0, min(100.0, score))
    score = round(score, 1)

    centre.trust_score = score

    # Update compliance status
    if score >= 85.0:
        centre.compliance_status = "Normal"
    elif score >= 60.0:
        centre.compliance_status = "Warning"
    else:
        centre.compliance_status = "Critical"

    return score
