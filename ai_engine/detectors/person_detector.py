"""
Person Detector Module
Uses YOLOv8 for person detection and headcount estimation.

Key Features:
- Aggregate headcount (privacy-preserving, no face recognition)
- Configurable confidence thresholds
- Region of Interest (ROI) masking for classroom areas
- Bounding box output for tracking integration
"""

import cv2
import numpy as np
from ultralytics import YOLO
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from pathlib import Path


@dataclass
class Detection:
    """A single object detection result."""
    id: int
    class_name: str
    confidence: float
    bbox: Tuple[int, int, int, int]  # x, y, w, h
    center: Tuple[int, int]  # cx, cy


@dataclass
class PersonDetectionResult:
    """Result of person detection on a single frame."""
    total_detected: int = 0
    confidence_avg: float = 0.0
    confidence_min: float = 0.0
    confidence_max: float = 0.0
    detections: List[Detection] = field(default_factory=list)
    annotated_frame: Optional[np.ndarray] = field(default=None, repr=False)
    roi_area: str = "full_frame"


class PersonDetector:
    """
    YOLO-based person detector for aggregate headcount estimation.
    
    Uses YOLOv8n (nano) by default for fast inference on CPU.
    Detects COCO class 0 (person) and computes aggregate counts.
    Privacy-preserving: only outputs counts and bounding boxes, no identity.
    """
    
    # COCO class index for 'person'
    PERSON_CLASS_ID = 0
    
    def __init__(
        self,
        model_path: str = "yolov8s.pt",
        confidence_threshold: float = 0.25,
        iou_threshold: float = 0.45,
        imgsz: int = 1280,
        device: str = "cpu"
    ):
        """
        Initialize the person detector.
        
        Args:
            model_path: Path to YOLO model weights (auto-downloads if not found)
            confidence_threshold: Minimum confidence for detections
            iou_threshold: IoU threshold for NMS
            device: Inference device ('cpu', 'cuda', '0', etc.)
        """
        self.confidence_threshold = confidence_threshold
        self.iou_threshold = iou_threshold
        self.imgsz = imgsz
        self.device = device
        
        print(f"[PersonDetector] Loading model: {model_path}")
        self.model = YOLO(model_path)
        print(f"[PersonDetector] Model loaded. Device: {device}")
    
    def detect(
        self,
        frame: np.ndarray,
        roi_mask: Optional[np.ndarray] = None,
        annotate: bool = True
    ) -> PersonDetectionResult:
        """
        Detect persons in a frame and return aggregate headcount.
        
        Args:
            frame: BGR image as numpy array
            roi_mask: Optional binary mask for Region of Interest
            annotate: Whether to draw bounding boxes on the frame
            
        Returns:
            PersonDetectionResult with count and detection details
        """
        # Run YOLO inference with larger image size for better small-person detection
        results = self.model(
            frame,
            conf=self.confidence_threshold,
            iou=self.iou_threshold,
            imgsz=self.imgsz,
            device=self.device,
            classes=[self.PERSON_CLASS_ID],  # Only detect persons
            verbose=False
        )
        
        result = results[0]
        detections = []
        
        if result.boxes is not None and len(result.boxes) > 0:
            boxes = result.boxes
            
            for i, box in enumerate(boxes):
                # Get bounding box coordinates
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
                conf = float(box.conf[0].cpu().numpy())
                
                w = x2 - x1
                h = y2 - y1
                cx = x1 + w // 2
                cy = y1 + h // 2
                
                # If ROI mask is provided, only count detections inside the ROI
                if roi_mask is not None:
                    if cy < roi_mask.shape[0] and cx < roi_mask.shape[1]:
                        if roi_mask[cy, cx] == 0:
                            continue  # Skip detections outside ROI
                
                detections.append(Detection(
                    id=i + 1,
                    class_name="person",
                    confidence=round(conf, 3),
                    bbox=(int(x1), int(y1), int(w), int(h)),
                    center=(int(cx), int(cy))
                ))
        
        # Calculate aggregate statistics
        total = len(detections)
        confidences = [d.confidence for d in detections]
        
        avg_conf = round(float(np.mean(confidences)), 3) if confidences else 0.0
        min_conf = round(float(np.min(confidences)), 3) if confidences else 0.0
        max_conf = round(float(np.max(confidences)), 3) if confidences else 0.0
        
        # Create annotated frame
        annotated = None
        if annotate:
            annotated = self._draw_detections(frame.copy(), detections, total)
        
        return PersonDetectionResult(
            total_detected=total,
            confidence_avg=avg_conf,
            confidence_min=min_conf,
            confidence_max=max_conf,
            detections=detections,
            annotated_frame=annotated,
            roi_area="full_frame" if roi_mask is None else "roi_masked"
        )
    
    def _draw_detections(
        self,
        frame: np.ndarray,
        detections: List[Detection],
        total_count: int
    ) -> np.ndarray:
        """
        Draw bounding boxes and count overlay on the frame.
        
        Args:
            frame: BGR image to annotate
            detections: List of Detection objects
            total_count: Total person count
            
        Returns:
            Annotated frame
        """
        for det in detections:
            x, y, w, h = det.bbox
            color = (0, 255, 0)  # Green
            
            # Draw bounding box
            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
            
            # Draw confidence label
            label = f"P{det.id} {det.confidence:.0%}"
            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]
            cv2.rectangle(frame, (x, y - label_size[1] - 8), (x + label_size[0] + 4, y), color, -1)
            cv2.putText(frame, label, (x + 2, y - 4),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
            
            # Draw center point
            cv2.circle(frame, det.center, 4, (0, 0, 255), -1)
        
        # Draw total count overlay (top-left)
        count_text = f"Persons Detected: {total_count}"
        cv2.rectangle(frame, (5, 5), (350, 50), (0, 0, 0), -1)
        cv2.putText(frame, count_text, (15, 38),
                   cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)
        
        return frame
    
    def create_roi_mask(
        self,
        frame_shape: Tuple[int, int],
        roi_polygon: List[Tuple[int, int]]
    ) -> np.ndarray:
        """
        Create a binary ROI mask from a polygon.
        Useful for masking out doors, windows, corridors.
        
        Args:
            frame_shape: (height, width) of the frame
            roi_polygon: List of (x, y) points defining the ROI
            
        Returns:
            Binary mask where 255 = inside ROI
        """
        mask = np.zeros(frame_shape[:2], dtype=np.uint8)
        pts = np.array(roi_polygon, dtype=np.int32)
        cv2.fillPoly(mask, [pts], 255)
        return mask
