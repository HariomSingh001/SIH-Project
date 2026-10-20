"""
SQLAlchemy ORM Models for Parman AI Backend.
Defines tables for Centres, Batches, Cameras, Attendance, Equipment, Telemetry, and Discrepancy Alerts.
"""

from datetime import datetime
from typing import List, Optional
from sqlalchemy import (
    String, Integer, Float, Boolean, DateTime, ForeignKey, Text, JSON
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..core.database import Base


class Centre(Base):
    __tablename__ = "centres"

    centre_id: Mapped[str] = mapped_column(String(50), primary_key=True, index=True)
    centre_name: Mapped[str] = mapped_column(String(200), nullable=False)
    state: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    district: Mapped[str] = mapped_column(String(100), nullable=False)
    address: Mapped[str] = mapped_column(Text, nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    centre_type: Mapped[str] = mapped_column(String(50), default="PMKVY")
    empanelment_status: Mapped[str] = mapped_column(String(50), default="Active", index=True)
    total_capacity: Mapped[int] = mapped_column(Integer, default=0)
    active_batches: Mapped[int] = mapped_column(Integer, default=0)
    sector: Mapped[str] = mapped_column(String(100), nullable=False)
    connectivity: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    contact_person: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    contact_phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    trust_score: Mapped[float] = mapped_column(Float, default=100.0, index=True)
    last_physical_audit: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    compliance_status: Mapped[str] = mapped_column(String(50), default="Normal", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    batches: Mapped[List["Batch"]] = relationship("Batch", back_populates="centre", cascade="all, delete-orphan")
    cameras: Mapped[List["Camera"]] = relationship("Camera", back_populates="centre", cascade="all, delete-orphan")
    attendance_records: Mapped[List["AttendanceRecord"]] = relationship("AttendanceRecord", back_populates="centre", cascade="all, delete-orphan")
    equipment_records: Mapped[List["SanctionedEquipment"]] = relationship("SanctionedEquipment", back_populates="centre", cascade="all, delete-orphan")
    telemetry_records: Mapped[List["TelemetryRecord"]] = relationship("TelemetryRecord", back_populates="centre", cascade="all, delete-orphan")
    discrepancy_alerts: Mapped[List["DiscrepancyAlert"]] = relationship("DiscrepancyAlert", back_populates="centre", cascade="all, delete-orphan")


class Batch(Base):
    __tablename__ = "batches"

    batch_id: Mapped[str] = mapped_column(String(50), primary_key=True, index=True)
    centre_id: Mapped[str] = mapped_column(String(50), ForeignKey("centres.centre_id", ondelete="CASCADE"), index=True)
    course_id: Mapped[str] = mapped_column(String(50), nullable=False)
    course_name: Mapped[str] = mapped_column(String(200), nullable=False)
    batch_size: Mapped[int] = mapped_column(Integer, default=30)
    start_date: Mapped[str] = mapped_column(String(50), nullable=False)
    end_date: Mapped[str] = mapped_column(String(50), nullable=False)
    shift: Mapped[str] = mapped_column(String(100), nullable=False)

    # Relationships
    centre: Mapped["Centre"] = relationship("Centre", back_populates="batches")


class Camera(Base):
    __tablename__ = "cameras"

    camera_id: Mapped[str] = mapped_column(String(50), primary_key=True, index=True)
    centre_id: Mapped[str] = mapped_column(String(50), ForeignKey("centres.centre_id", ondelete="CASCADE"), index=True)
    location: Mapped[str] = mapped_column(String(100), nullable=False)
    type: Mapped[str] = mapped_column(String(50), default="Indoor")
    resolution: Mapped[str] = mapped_column(String(50), default="1080p")
    status: Mapped[str] = mapped_column(String(50), default="Active")

    # Relationships
    centre: Mapped["Centre"] = relationship("Centre", back_populates="cameras")


class AttendanceRecord(Base):
    __tablename__ = "attendance_records"

    record_id: Mapped[str] = mapped_column(String(100), primary_key=True, index=True)
    centre_id: Mapped[str] = mapped_column(String(50), ForeignKey("centres.centre_id", ondelete="CASCADE"), index=True)
    batch_id: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    course_name: Mapped[str] = mapped_column(String(200), nullable=False)
    date: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    shift: Mapped[str] = mapped_column(String(100), nullable=False)
    claimed_attendance: Mapped[int] = mapped_column(Integer, nullable=False)
    batch_capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    attendance_percentage: Mapped[float] = mapped_column(Float, default=0.0)
    submitted_by: Mapped[str] = mapped_column(String(100), nullable=False)
    submitted_at: Mapped[str] = mapped_column(String(100), nullable=False)
    ai_detected_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    discrepancy: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    verification_status: Mapped[str] = mapped_column(String(50), default="Pending", index=True)  # Verified, Discrepancy, Pending
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    centre: Mapped["Centre"] = relationship("Centre", back_populates="attendance_records")


class SanctionedEquipment(Base):
    __tablename__ = "sanctioned_equipment"

    item_id: Mapped[str] = mapped_column(String(50), primary_key=True, index=True)
    centre_id: Mapped[str] = mapped_column(String(50), ForeignKey("centres.centre_id", ondelete="CASCADE"), index=True)
    item_name: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    sanctioned_count: Mapped[int] = mapped_column(Integer, nullable=False)
    minimum_required: Mapped[int] = mapped_column(Integer, nullable=False)
    location: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="Mandatory")
    last_verified: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    last_verified_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    centre: Mapped["Centre"] = relationship("Centre", back_populates="equipment_records")


class TelemetryRecord(Base):
    __tablename__ = "telemetry_records"

    telemetry_id: Mapped[str] = mapped_column(String(100), primary_key=True, index=True)
    centre_id: Mapped[str] = mapped_column(String(50), ForeignKey("centres.centre_id", ondelete="CASCADE"), index=True)
    camera_id: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    camera_location: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    batch_id: Mapped[Optional[str]] = mapped_column(String(50), index=True, nullable=True)
    timestamp: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    frame_index: Mapped[int] = mapped_column(Integer, default=0)
    total_detected_persons: Mapped[int] = mapped_column(Integer, default=0)
    confidence_avg: Mapped[float] = mapped_column(Float, default=0.0)
    roi_area: Mapped[Optional[str]] = mapped_column(String(100), default="full_frame")
    bounding_boxes: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    equipment_detected: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    evidence_frame_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    privacy_masked: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    centre: Mapped["Centre"] = relationship("Centre", back_populates="telemetry_records")


class DiscrepancyAlert(Base):
    __tablename__ = "discrepancy_alerts"

    alert_id: Mapped[str] = mapped_column(String(100), primary_key=True, index=True)
    centre_id: Mapped[str] = mapped_column(String(50), ForeignKey("centres.centre_id", ondelete="CASCADE"), index=True)
    batch_id: Mapped[Optional[str]] = mapped_column(String(50), index=True, nullable=True)
    record_id: Mapped[Optional[str]] = mapped_column(String(100), index=True, nullable=True)
    timestamp: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    alert_type: Mapped[str] = mapped_column(String(100), index=True, nullable=False)  # ATTENDANCE_DEFICIT, GHOST_BATCH, EQUIPMENT_SHORTAGE
    severity: Mapped[str] = mapped_column(String(50), index=True, nullable=False)     # Normal, Warning, Critical
    claimed_value: Mapped[float] = mapped_column(Float, default=0.0)
    detected_value: Mapped[float] = mapped_column(Float, default=0.0)
    difference: Mapped[float] = mapped_column(Float, default=0.0)
    percentage_gap: Mapped[float] = mapped_column(Float, default=0.0)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="Open", index=True)       # Open, Acknowledged, Resolved, Escalated
    evidence_frame_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    centre: Mapped["Centre"] = relationship("Centre", back_populates="discrepancy_alerts")
