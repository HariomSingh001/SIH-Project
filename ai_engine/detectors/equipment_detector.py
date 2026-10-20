"""
Equipment / Infrastructure Detector Module
Uses YOLOv8 for detecting sanctioned equipment items.

Key Features:
- Detects common classroom/lab equipment using COCO pretrained classes
- Custom class mapping for training centre equipment categories
- Inventory cross-verification against sanctioned lists
- Operability estimation via optical flow (motion detection)
"""

import cv2
import numpy as np
from ultralytics import YOLO
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple


@dataclass
class EquipmentDetection:
    """A single equipment detection."""
    class_name: str
    mapped_category: str
    count: int
    confidence_avg: float
    bounding_boxes: List[Tuple[int, int, int, int]] = field(default_factory=list)


@dataclass
class EquipmentResult:
    """Result of equipment detection on a single frame."""
    items_detected: List[EquipmentDetection] = field(default_factory=list)
    total_unique_classes: int = 0
    equipment_activity: Dict = field(default_factory=dict)
    annotated_frame: Optional[np.ndarray] = field(default=None, repr=False)


# Mapping from COCO classes to training centre equipment categories
COCO_TO_EQUIPMENT_MAP = {
    # IT Equipment
    "laptop": "Desktop/Laptop Computer",
    "tv": "Monitor/Display Screen",
    "keyboard": "Keyboard",
    "mouse": "Mouse",
    "cell phone": "Mobile Device",
    
    # Furniture
    "chair": "Student Chair",
    "dining table": "Desk/Table",
    "bench": "Workbench",
    "couch": "Seating",
    
    # Teaching Aids
    "book": "Study Material",
    "clock": "Wall Clock",
    
    # Safety Equipment
    "fire hydrant": "Fire Safety Equipment",
    "backpack": "Student Bag",
    "handbag": "Bag",
    
    # Workshop / Lab (mapped from closest COCO classes)
    "scissors": "Cutting Tool",
    "bottle": "Lab Bottle/Container",
    "cup": "Cup/Beaker",
    "vase": "Container",
    
    # General
    "person": None,  # Handled by PersonDetector, skip here
}

# COCO class IDs we're interested in for equipment detection
EQUIPMENT_COCO_IDS = [
    56,  # chair
    57,  # couch (sofa)
    59,  # bed -> bench/table mapping
    60,  # dining table
    62,  # tv/monitor
    63,  # laptop
    64,  # mouse
    65,  # remote
    66,  # keyboard
    67,  # cell phone
    73,  # book
    74,  # clock
    76,  # scissors
    39,  # bottle
    41,  # cup
    10,  # fire hydrant
    24,  # backpack
    26,  # handbag
]


class EquipmentDetector:
    """
    YOLO-based equipment and infrastructure detector.
    
    Uses YOLOv8 pretrained on COCO to detect common objects found in
    training centres (chairs, desks, monitors, laptops, etc.)
    and maps them to training centre equipment categories.
    
    For a production system, this would be fine-tuned on custom
    training centre equipment classes (sewing machines, soldering stations, etc.)
    """
    
    def __init__(
        self,
        model_path: str = "yolov8n.pt",
        confidence_threshold: float = 0.30,
        iou_threshold: float = 0.45,
        device: str = "cpu"
    ):
        """
        Initialize the equipment detector.
        
        Args:
            model_path: Path to YOLO model weights
            confidence_threshold: Minimum confidence for detections
            iou_threshold: IoU threshold for NMS
            device: Inference device
        """
        self.confidence_threshold = confidence_threshold
        self.iou_threshold = iou_threshold
        self.device = device
        self._prev_gray = None
        
        print(f"[EquipmentDetector] Loading model: {model_path}")
        self.model = YOLO(model_path)
        print(f"[EquipmentDetector] Model loaded for equipment detection")
    
    def detect(
        self,
        frame: np.ndarray,
        annotate: bool = True
    ) -> EquipmentResult:
        """
        Detect equipment/infrastructure items in a frame.
        
        Args:
            frame: BGR image as numpy array
            annotate: Whether to draw bounding boxes
            
        Returns:
            EquipmentResult with detected items and counts
        """
        # Run YOLO inference for equipment classes
        results = self.model(
            frame,
            conf=self.confidence_threshold,
            iou=self.iou_threshold,
            device=self.device,
            classes=EQUIPMENT_COCO_IDS,
            verbose=False
        )
        
        result = results[0]
        
        # Group detections by class
        class_detections: Dict[str, List] = {}
        
        if result.boxes is not None and len(result.boxes) > 0:
            boxes = result.boxes
            names = result.names
            
            for box in boxes:
                cls_id = int(box.cls[0].cpu().numpy())
                cls_name = names.get(cls_id, f"class_{cls_id}")
                conf = float(box.conf[0].cpu().numpy())
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
                
                # Skip 'person' class
                if cls_name == "person":
                    continue
                
                if cls_name not in class_detections:
                    class_detections[cls_name] = {
                        "confidences": [],
                        "bboxes": []
                    }
                
                class_detections[cls_name]["confidences"].append(conf)
                class_detections[cls_name]["bboxes"].append(
                    (int(x1), int(y1), int(x2 - x1), int(y2 - y1))
                )
        
        # Build equipment detection list
        items = []
        for cls_name, data in class_detections.items():
            mapped = COCO_TO_EQUIPMENT_MAP.get(cls_name, cls_name.title())
            if mapped is None:
                continue  # Skip explicitly excluded classes
            
            items.append(EquipmentDetection(
                class_name=cls_name,
                mapped_category=mapped,
                count=len(data["confidences"]),
                confidence_avg=round(float(np.mean(data["confidences"])), 3),
                bounding_boxes=data["bboxes"]
            ))
        
        # Sort by count descending
        items.sort(key=lambda x: x.count, reverse=True)
        
        # Compute equipment activity/operability via optical flow
        activity = self._estimate_activity(frame)
        
        # Create annotated frame
        annotated = None
        if annotate:
            annotated = self._draw_equipment(frame.copy(), items)
        
        return EquipmentResult(
            items_detected=items,
            total_unique_classes=len(items),
            equipment_activity=activity,
            annotated_frame=annotated
        )
    
    def _estimate_activity(self, frame: np.ndarray) -> Dict:
        """
        Estimate equipment activity using optical flow / frame differencing.
        This helps verify that equipment is not just present but actively used.
        
        Args:
            frame: BGR image
            
        Returns:
            Activity metrics dictionary
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (15, 15), 0)
        
        if self._prev_gray is None:
            self._prev_gray = gray
            return {
                "motion_detected": False,
                "active_zones": 0,
                "activity_level": "unknown"
            }
        
        # Frame difference for motion detection
        diff = cv2.absdiff(self._prev_gray, gray)
        _, thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)
        
        # Count motion regions
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        significant_contours = [c for c in contours if cv2.contourArea(c) > 500]
        
        motion_percentage = float(np.sum(thresh > 0)) / thresh.size * 100
        
        self._prev_gray = gray
        
        # Classify activity level
        if motion_percentage > 5.0:
            level = "high"
        elif motion_percentage > 1.0:
            level = "moderate"
        elif motion_percentage > 0.1:
            level = "low"
        else:
            level = "static"
        
        return {
            "motion_detected": len(significant_contours) > 0,
            "active_zones": len(significant_contours),
            "motion_percentage": round(motion_percentage, 2),
            "activity_level": level
        }
    
    def _draw_equipment(
        self,
        frame: np.ndarray,
        items: List[EquipmentDetection]
    ) -> np.ndarray:
        """Draw equipment bounding boxes with category labels."""
        # Color map for different categories
        colors = {
            "Desktop/Laptop Computer": (255, 165, 0),  # Orange
            "Monitor/Display Screen": (0, 165, 255),    # Orange-Blue
            "Student Chair": (147, 20, 255),             # Pink
            "Desk/Table": (255, 255, 0),                 # Cyan
            "Keyboard": (0, 255, 255),                   # Yellow
            "Study Material": (128, 0, 128),             # Purple
            "Fire Safety Equipment": (0, 0, 255),        # Red
        }
        default_color = (200, 200, 200)
        
        for item in items:
            color = colors.get(item.mapped_category, default_color)
            for bbox in item.bounding_boxes:
                x, y, w, h = bbox
                cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
                
                label = f"{item.mapped_category} ({item.confidence_avg:.0%})"
                label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.4, 1)[0]
                cv2.rectangle(frame, (x, y + h), (x + label_size[0] + 4, y + h + label_size[1] + 8), color, -1)
                cv2.putText(frame, label, (x + 2, y + h + label_size[1] + 4),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 0), 1)
        
        # Draw summary overlay (top-right area)
        y_offset = 60
        cv2.rectangle(frame, (frame.shape[1] - 320, 5), (frame.shape[1] - 5, y_offset + len(items) * 25 + 10), (0, 0, 0), -1)
        cv2.putText(frame, "Equipment Detected:", (frame.shape[1] - 310, y_offset - 15),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        
        for i, item in enumerate(items):
            text = f"{item.mapped_category}: {item.count}"
            color = colors.get(item.mapped_category, default_color)
            cv2.putText(frame, text, (frame.shape[1] - 310, y_offset + 10 + i * 25),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        
        return frame
    
    def cross_check_inventory(
        self,
        detection_result: EquipmentResult,
        sanctioned_inventory: List[Dict]
    ) -> List[Dict]:
        """
        Cross-check detected equipment against sanctioned inventory.
        
        Args:
            detection_result: Output from detect()
            sanctioned_inventory: List of sanctioned equipment items
            
        Returns:
            List of compliance check results
        """
        compliance = []
        
        detected_map = {
            item.mapped_category: item.count 
            for item in detection_result.items_detected
        }
        
        for item in sanctioned_inventory:
            item_name = item.get("item_name", "Unknown")
            required = item.get("minimum_required", 0)
            sanctioned = item.get("sanctioned_count", 0)
            
            # Try to match with detected items (fuzzy matching)
            detected_count = 0
            for category, count in detected_map.items():
                if any(keyword in item_name.lower() for keyword in category.lower().split()):
                    detected_count = count
                    break
            
            status = "Compliant" if detected_count >= required else "Non-Compliant"
            if detected_count == 0 and required > 0:
                status = "Not Detected"
            
            compliance.append({
                "item_name": item_name,
                "sanctioned_count": sanctioned,
                "minimum_required": required,
                "detected_count": detected_count,
                "status": status,
                "deficit": max(0, required - detected_count)
            })
        
        return compliance
