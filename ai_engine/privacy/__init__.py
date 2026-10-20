"""
Privacy Engine - Face Blurring Module
DPDP Act 2023 compliant privacy-preserving engine.

Key Features:
- Automatic face detection and Gaussian blurring
- Configurable blur intensity
- All evidence frames are privacy-masked before storage/transmission
- Only aggregate counts are transmitted, never individual identities
"""

import cv2
import numpy as np
from ultralytics import YOLO
from dataclasses import dataclass
from typing import List, Tuple, Optional


@dataclass
class PrivacyResult:
    """Result of privacy processing on a frame."""
    blurred_frame: np.ndarray
    faces_detected: int
    faces_blurred: int
    blur_method: str
    blur_kernel_size: int
    pii_detected: bool


class FaceBlurEngine:
    """
    Privacy-preserving face blurring engine.
    
    Automatically detects faces in frames and applies Gaussian blur
    before any storage or transmission. This ensures DPDP Act compliance
    by preventing individual identification from evidence frames.
    
    Detection Methods:
    1. YOLO face detection (more accurate, uses same model infrastructure)
    2. OpenCV Haar Cascade (fallback, lighter weight)
    """
    
    def __init__(
        self,
        blur_kernel_size: int = 51,
        blur_strength: float = 30.0,
        method: str = "haar",
        yolo_model_path: str = "yolov8n-face.pt",
        expand_ratio: float = 0.3
    ):
        """
        Initialize the face blur engine.
        
        Args:
            blur_kernel_size: Size of the Gaussian blur kernel (must be odd)
            blur_strength: Sigma for Gaussian blur (higher = more blur)
            method: Detection method - 'haar' or 'yolo'
            yolo_model_path: Path to YOLO face model (if method='yolo')
            expand_ratio: How much to expand face bounding box (0.3 = 30% larger)
        """
        self.blur_kernel_size = blur_kernel_size if blur_kernel_size % 2 == 1 else blur_kernel_size + 1
        self.blur_strength = blur_strength
        self.method = method
        self.expand_ratio = expand_ratio
        
        if method == "haar":
            # Use OpenCV's built-in Haar Cascade for face detection
            cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
            self.face_cascade = cv2.CascadeClassifier(cascade_path)
            
            # Also load profile face cascade for side views
            profile_path = cv2.data.haarcascades + "haarcascade_profileface.xml"
            self.profile_cascade = cv2.CascadeClassifier(profile_path)
            
            print(f"[FaceBlurEngine] Using Haar Cascade face detection")
        else:
            # Use YOLO for face detection
            self.face_model = YOLO(yolo_model_path)
            print(f"[FaceBlurEngine] Using YOLO face detection: {yolo_model_path}")
        
        print(f"[FaceBlurEngine] Blur kernel: {self.blur_kernel_size}, expand: {self.expand_ratio}")
    
    def blur_faces(
        self,
        frame: np.ndarray,
        person_detections: Optional[List] = None
    ) -> PrivacyResult:
        """
        Detect and blur all faces in a frame.
        
        Args:
            frame: BGR image as numpy array
            person_detections: Optional list of person Detection objects to help 
                              locate face regions (from PersonDetector)
            
        Returns:
            PrivacyResult with blurred frame and metadata
        """
        blurred_frame = frame.copy()
        face_regions = []
        
        if self.method == "haar":
            face_regions = self._detect_faces_haar(frame)
        else:
            face_regions = self._detect_faces_yolo(frame)
        
        # If person detections are provided but few faces detected,
        # also blur the upper portion of each person bounding box
        # (catches cases where face is turned away or partially occluded)
        if person_detections and len(face_regions) < len(person_detections) * 0.5:
            for det in person_detections:
                x, y, w, h = det.bbox
                # Upper 30% of person bbox is likely the head/face area
                head_h = int(h * 0.3)
                head_region = (x, y, w, head_h)
                
                # Check if this region overlaps with any detected face
                is_covered = False
                for fx, fy, fw, fh in face_regions:
                    overlap_x = max(0, min(x + w, fx + fw) - max(x, fx))
                    overlap_y = max(0, min(y + head_h, fy + fh) - max(y, fy))
                    if overlap_x > 0 and overlap_y > 0:
                        is_covered = True
                        break
                
                if not is_covered:
                    face_regions.append(head_region)
        
        # Apply blur to all detected face regions
        faces_blurred = 0
        for (x, y, w, h) in face_regions:
            # Expand the region slightly
            ex = int(w * self.expand_ratio)
            ey = int(h * self.expand_ratio)
            
            x1 = max(0, x - ex)
            y1 = max(0, y - ey)
            x2 = min(frame.shape[1], x + w + ex)
            y2 = min(frame.shape[0], y + h + ey)
            
            if x2 > x1 and y2 > y1:
                # Apply strong Gaussian blur to the face region
                face_roi = blurred_frame[y1:y2, x1:x2]
                blurred_roi = cv2.GaussianBlur(
                    face_roi,
                    (self.blur_kernel_size, self.blur_kernel_size),
                    self.blur_strength
                )
                # Apply blur twice for extra privacy
                blurred_roi = cv2.GaussianBlur(
                    blurred_roi,
                    (self.blur_kernel_size, self.blur_kernel_size),
                    self.blur_strength
                )
                blurred_frame[y1:y2, x1:x2] = blurred_roi
                faces_blurred += 1
        
        return PrivacyResult(
            blurred_frame=blurred_frame,
            faces_detected=len(face_regions),
            faces_blurred=faces_blurred,
            blur_method="gaussian",
            blur_kernel_size=self.blur_kernel_size,
            pii_detected=len(face_regions) > 0
        )
    
    def _detect_faces_haar(self, frame: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """
        Detect faces using OpenCV Haar Cascades.
        
        Returns:
            List of (x, y, w, h) tuples for each detected face
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.equalizeHist(gray)
        
        # Frontal face detection
        frontal_faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=4,
            minSize=(20, 20),
            flags=cv2.CASCADE_SCALE_IMAGE
        )
        
        # Profile face detection
        profile_faces = self.profile_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=4,
            minSize=(20, 20),
            flags=cv2.CASCADE_SCALE_IMAGE
        )
        
        # Also detect on flipped image for left-side profiles
        flipped = cv2.flip(gray, 1)
        flipped_profiles = self.profile_cascade.detectMultiScale(
            flipped,
            scaleFactor=1.1,
            minNeighbors=4,
            minSize=(20, 20),
            flags=cv2.CASCADE_SCALE_IMAGE
        )
        
        all_faces = []
        
        # Add frontal faces
        if len(frontal_faces) > 0:
            all_faces.extend([(x, y, w, h) for (x, y, w, h) in frontal_faces])
        
        # Add profile faces
        if len(profile_faces) > 0:
            all_faces.extend([(x, y, w, h) for (x, y, w, h) in profile_faces])
        
        # Add flipped profile faces (mirror x-coordinate back)
        if len(flipped_profiles) > 0:
            for (x, y, w, h) in flipped_profiles:
                mirrored_x = frame.shape[1] - x - w
                all_faces.append((mirrored_x, y, w, h))
        
        # Remove duplicates using NMS-style filtering
        all_faces = self._non_max_suppression(all_faces, overlap_thresh=0.3)
        
        return all_faces
    
    def _detect_faces_yolo(self, frame: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """Detect faces using YOLO face model."""
        results = self.face_model(frame, conf=0.25, verbose=False)
        faces = []
        
        if results[0].boxes is not None:
            for box in results[0].boxes:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
                faces.append((int(x1), int(y1), int(x2 - x1), int(y2 - y1)))
        
        return faces
    
    def _non_max_suppression(
        self,
        boxes: List[Tuple[int, int, int, int]],
        overlap_thresh: float = 0.3
    ) -> List[Tuple[int, int, int, int]]:
        """
        Simple NMS to remove duplicate face detections.
        
        Args:
            boxes: List of (x, y, w, h) bounding boxes
            overlap_thresh: IoU threshold for suppression
            
        Returns:
            Filtered list of bounding boxes
        """
        if len(boxes) == 0:
            return []
        
        boxes_array = np.array(boxes)
        x1 = boxes_array[:, 0]
        y1 = boxes_array[:, 1]
        x2 = x1 + boxes_array[:, 2]
        y2 = y1 + boxes_array[:, 3]
        
        areas = boxes_array[:, 2] * boxes_array[:, 3]
        order = areas.argsort()[::-1]
        
        keep = []
        while len(order) > 0:
            i = order[0]
            keep.append(i)
            
            if len(order) == 1:
                break
            
            xx1 = np.maximum(x1[i], x1[order[1:]])
            yy1 = np.maximum(y1[i], y1[order[1:]])
            xx2 = np.minimum(x2[i], x2[order[1:]])
            yy2 = np.minimum(y2[i], y2[order[1:]])
            
            inter = np.maximum(0, xx2 - xx1) * np.maximum(0, yy2 - yy1)
            union = areas[i] + areas[order[1:]] - inter
            iou = inter / (union + 1e-6)
            
            remaining = np.where(iou <= overlap_thresh)[0]
            order = order[remaining + 1]
        
        return [boxes[i] for i in keep]
