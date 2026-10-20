"""
Pydantic schemas for request/response serialization and validation.
"""

from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field
from datetime import datetime


# ==========================================
# BATCH & CAMERA SCHEMAS
# ==========================================

class BatchSchema(BaseModel):
    batch_id: str
    course_id: str
    course_name: str
    batch_size: int
    start_date: str
    end_date: str
    shift: str

    class Config:
        from_attributes = True


class CameraSchema(BaseModel):
    camera_id: str
    location: str
    type: str = "Indoor"
    resolution: str = "1080p"
    status: str = "Active"

    class Config:
        from_attributes = True


# ==========================================
# CENTRE SCHEMAS
# ==========================================

class CentreBase(BaseModel):
    centre_id: str
    centre_name: str
    state: str
    city: str
    district: str
    address: str
    latitude: float
    longitude: float
    centre_type: str = "PMKVY"
    empanelment_status: str = "Active"
    total_capacity: int = 0
    active_batches: int = 0
    sector: str
    connectivity: Optional[str] = None
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    trust_score: float = 100.0
    last_physical_audit: Optional[str] = None
    compliance_status: str = "Normal"


class CentreCreate(CentreBase):
    courses: Optional[List[BatchSchema]] = None
    cameras: Optional[List[CameraSchema]] = None


class CentreUpdate(BaseModel):
    centre_name: Optional[str] = None
    empanelment_status: Optional[str] = None
    total_capacity: Optional[int] = None
    active_batches: Optional[int] = None
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    trust_score: Optional[float] = None
    compliance_status: Optional[str] = None


class CentreResponse(CentreBase):
    class Config:
        from_attributes = True


class CentreDetailResponse(CentreBase):
    batches: List[BatchSchema] = []
    cameras: List[CameraSchema] = []

    class Config:
        from_attributes = True


# ==========================================
# ATTENDANCE SCHEMAS
# ==========================================

class AttendanceBase(BaseModel):
    record_id: str
    centre_id: str
    batch_id: str
    course_name: str
    date: str
    shift: str
    claimed_attendance: int
    batch_capacity: int
    attendance_percentage: float
    submitted_by: str
    submitted_at: str
    ai_detected_count: Optional[int] = None
    discrepancy: Optional[int] = None
    verification_status: str = "Pending"
    notes: Optional[str] = None


class AttendanceCreate(AttendanceBase):
    pass


class AttendanceResponse(AttendanceBase):
    class Config:
        from_attributes = True


# ==========================================
# EQUIPMENT SCHEMAS
# ==========================================

class EquipmentBase(BaseModel):
    item_id: str
    centre_id: str
    item_name: str
    category: str
    sanctioned_count: int
    minimum_required: int
    location: str
    status: str = "Mandatory"
    last_verified: Optional[str] = None
    last_verified_count: Optional[int] = None
    notes: Optional[str] = None


class EquipmentCreate(EquipmentBase):
    pass


class EquipmentUpdate(BaseModel):
    last_verified: Optional[str] = None
    last_verified_count: Optional[int] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class EquipmentResponse(EquipmentBase):
    class Config:
        from_attributes = True


# ==========================================
# TELEMETRY SCHEMAS
# ==========================================

class TelemetryPayload(BaseModel):
    telemetry_id: Optional[str] = None
    centre_id: str
    camera_id: str
    camera_location: Optional[str] = "Classroom"
    batch_id: Optional[str] = None
    timestamp: str
    frame_index: int = 0
    total_detected_persons: int
    confidence_avg: float = 0.0
    roi_area: Optional[str] = "full_frame"
    bounding_boxes: Optional[Any] = None
    equipment_detected: Optional[Any] = None
    evidence_frame_path: Optional[str] = None
    privacy_masked: bool = True


class TelemetryResponse(BaseModel):
    telemetry_id: str
    centre_id: str
    camera_id: str
    camera_location: Optional[str] = None
    batch_id: Optional[str] = None
    timestamp: str
    frame_index: int
    total_detected_persons: int
    confidence_avg: float
    roi_area: Optional[str]
    equipment_detected: Optional[Any] = None
    evidence_frame_path: Optional[str] = None
    privacy_masked: bool

    class Config:
        from_attributes = True


# ==========================================
# DISCREPANCY SCHEMAS
# ==========================================

class DiscrepancyAlertBase(BaseModel):
    alert_id: str
    centre_id: str
    batch_id: Optional[str] = None
    record_id: Optional[str] = None
    timestamp: str
    alert_type: str
    severity: str
    claimed_value: float
    detected_value: float
    difference: float
    percentage_gap: float
    description: str
    status: str = "Open"
    evidence_frame_path: Optional[str] = None


class DiscrepancyAlertCreate(DiscrepancyAlertBase):
    pass


class DiscrepancyAlertUpdate(BaseModel):
    status: str  # Open, Acknowledged, Resolved, Escalated


class DiscrepancyAlertResponse(DiscrepancyAlertBase):
    centre_name: Optional[str] = None

    class Config:
        from_attributes = True


# ==========================================
# DASHBOARD & ANALYTICS SCHEMAS
# ==========================================

class CentreMapMarker(BaseModel):
    centre_id: str
    centre_name: str
    state: str
    city: str
    latitude: float
    longitude: float
    trust_score: float
    compliance_status: str
    active_batches: int
    total_capacity: int
    critical_alerts_count: int = 0


class NationalStatsResponse(BaseModel):
    total_centres: int
    active_centres: int
    monitored_batches: int
    total_capacity_monitored: int
    national_average_trust_score: float
    total_open_alerts: int
    critical_alerts_count: int
    warning_alerts_count: int
    attendance_verification_rate: float
    equipment_compliance_rate: float
    low_bandwidth_savings_pct: float = 97.3
