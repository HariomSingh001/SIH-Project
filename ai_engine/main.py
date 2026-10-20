"""
Parman AI Engine - Main Pipeline
Processes video feeds and produces privacy-masked telemetry output.

Pipeline Flow:
  Video File -> Frame Sampler -> Person Detector -> Equipment Detector 
  -> Face Blur -> Telemetry JSON + Evidence Frames

Usage:
  python main.py --video <path> [--output <dir>] [--interval <seconds>]
"""

import json
import sys
import os
import argparse
import time
from pathlib import Path
from datetime import datetime, timezone, timedelta

import cv2
import numpy as np

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ai_engine.sampler import FrameSampler
from ai_engine.detectors.person_detector import PersonDetector
from ai_engine.detectors.equipment_detector import EquipmentDetector
from ai_engine.privacy import FaceBlurEngine


class ParmanAIPipeline:
    """
    End-to-end video analytics pipeline for training centre monitoring.
    
    Processes video frames and produces:
    1. Aggregate headcount (privacy-preserving)
    2. Equipment detection and inventory cross-check
    3. Privacy-blurred evidence frames
    4. Structured telemetry JSON
    """
    
    def __init__(
        self,
        sampling_interval: float = 2.0,
        person_confidence: float = 0.35,
        equipment_confidence: float = 0.30,
        blur_kernel: int = 51,
        device: str = "cpu",
        centre_id: str = "CTR-DEMO-001",
        camera_id: str = "CAM-DEMO-01"
    ):
        """
        Initialize all pipeline components.
        
        Args:
            sampling_interval: Seconds between frame samples
            person_confidence: Min confidence for person detection
            equipment_confidence: Min confidence for equipment detection
            blur_kernel: Gaussian blur kernel size for face masking
            device: 'cpu' or 'cuda'
            centre_id: Training centre identifier
            camera_id: Camera identifier
        """
        self.centre_id = centre_id
        self.camera_id = camera_id
        
        print("=" * 60)
        print("  PARMAN AI ENGINE v0.1.0")
        print("  Privacy-Preserving Training Centre Monitor")
        print("=" * 60)
        print()
        
        # Initialize components
        print("[Pipeline] Initializing components...")
        
        self.sampler = FrameSampler(
            sampling_interval=sampling_interval,
            min_interval=max(1.0, sampling_interval / 3),
            motion_threshold=25.0
        )
        
        self.person_detector = PersonDetector(
            model_path="yolov8s.pt",
            confidence_threshold=person_confidence,
            imgsz=1280,
            device=device
        )
        
        self.equipment_detector = EquipmentDetector(
            confidence_threshold=equipment_confidence,
            device=device
        )
        
        self.face_blur = FaceBlurEngine(
            blur_kernel_size=blur_kernel,
            method="haar"
        )
        
        print("[Pipeline] All components initialized successfully!")
        print()
    
    def process_video(
        self,
        video_path: str,
        output_dir: str = "output",
        max_frames: int = None,
        save_evidence: bool = True,
        save_annotated: bool = True
    ) -> dict:
        """
        Process a video file through the entire pipeline.
        
        Args:
            video_path: Path to input video file
            output_dir: Directory for output files
            max_frames: Max frames to process (None = all)
            save_evidence: Whether to save blurred evidence frames
            save_annotated: Whether to save annotated detection frames
            
        Returns:
            Complete telemetry report as dictionary
        """
        video_path = str(Path(video_path).resolve())
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        evidence_dir = output_dir / "evidence"
        annotated_dir = output_dir / "annotated"
        evidence_dir.mkdir(exist_ok=True)
        annotated_dir.mkdir(exist_ok=True)
        
        print(f"[Pipeline] Processing: {video_path}")
        print(f"[Pipeline] Output dir: {output_dir}")
        print()
        
        # Get bandwidth stats
        bandwidth = self.sampler.get_bandwidth_stats(video_path)
        print(f"[Pipeline] Bandwidth saving: {bandwidth['bandwidth_saving_percent']}%")
        print(f"[Pipeline] Continuous stream: {bandwidth['continuous_stream_gb_per_day']} GB/day")
        print(f"[Pipeline] Smart sampling: {bandwidth['smart_sampling_mb_per_day']} MB/day")
        print()
        
        # Process frames
        all_telemetry = []
        frame_count = 0
        total_persons_detected = []
        all_equipment = {}
        processing_times = []
        
        IST = timezone(timedelta(hours=5, minutes=30))
        base_time = datetime.now(IST)
        
        for sampled_frame in self.sampler.sample_video(video_path, max_frames):
            frame_count += 1
            start_time = time.time()
            
            frame = sampled_frame.frame
            timestamp = base_time + timedelta(seconds=sampled_frame.timestamp_seconds)
            timestamp_str = timestamp.strftime("%Y-%m-%dT%H:%M:%S+05:30")
            
            print(f"\n--- Frame {frame_count} (index: {sampled_frame.frame_index}, "
                  f"t={sampled_frame.timestamp_seconds:.1f}s) ---")
            
            # Step 1: Person Detection
            person_result = self.person_detector.detect(frame, annotate=True)
            print(f"  [Person] Detected: {person_result.total_detected} persons "
                  f"(conf: {person_result.confidence_avg:.1%})")
            total_persons_detected.append(person_result.total_detected)
            
            # Step 2: Equipment Detection
            equip_result = self.equipment_detector.detect(frame, annotate=True)
            print(f"  [Equipment] Classes: {equip_result.total_unique_classes}, "
                  f"Activity: {equip_result.equipment_activity.get('activity_level', 'unknown')}")
            for item in equip_result.items_detected:
                print(f"    - {item.mapped_category}: {item.count} (conf: {item.confidence_avg:.1%})")
                key = item.mapped_category
                all_equipment[key] = max(all_equipment.get(key, 0), item.count)
            
            # Step 3: Privacy — Face Blurring
            privacy_result = self.face_blur.blur_faces(
                frame, 
                person_detections=person_result.detections
            )
            print(f"  [Privacy] Faces blurred: {privacy_result.faces_blurred}")
            
            # Step 4: Save evidence frames
            evidence_filename = f"{timestamp.strftime('%Y-%m-%d_%H-%M-%S')}_blurred.jpg"
            annotated_filename = f"{timestamp.strftime('%Y-%m-%d_%H-%M-%S')}_annotated.jpg"
            
            if save_evidence:
                evidence_path = evidence_dir / evidence_filename
                cv2.imwrite(str(evidence_path), privacy_result.blurred_frame)
            
            if save_annotated and person_result.annotated_frame is not None:
                annotated_path = annotated_dir / annotated_filename
                # Also blur faces on annotated frame
                annotated_blur = self.face_blur.blur_faces(
                    person_result.annotated_frame,
                    person_detections=person_result.detections
                )
                cv2.imwrite(str(annotated_path), annotated_blur.blurred_frame)
            
            # Calculate processing time
            proc_time = (time.time() - start_time) * 1000
            processing_times.append(proc_time)
            
            # Build telemetry record
            telemetry = {
                "telemetry_id": f"TEL-{timestamp.strftime('%Y%m%d-%H%M%S')}-{self.centre_id}",
                "centre_id": self.centre_id,
                "camera_id": self.camera_id,
                "timestamp": timestamp_str,
                "frame_index": sampled_frame.frame_index,
                "sampling_interval_seconds": self.sampler.sampling_interval,
                "person_detection": {
                    "total_detected": person_result.total_detected,
                    "confidence_avg": person_result.confidence_avg,
                    "confidence_min": person_result.confidence_min,
                    "confidence_max": person_result.confidence_max,
                    "roi_area": person_result.roi_area,
                    "bounding_boxes": [
                        {
                            "id": d.id,
                            "x": d.bbox[0], "y": d.bbox[1],
                            "w": d.bbox[2], "h": d.bbox[3],
                            "confidence": d.confidence
                        }
                        for d in person_result.detections
                    ]
                },
                "equipment_detection": {
                    "items_detected": [
                        {
                            "class": item.class_name,
                            "category": item.mapped_category,
                            "count": item.count,
                            "confidence_avg": item.confidence_avg
                        }
                        for item in equip_result.items_detected
                    ],
                    "equipment_activity": equip_result.equipment_activity
                },
                "privacy": {
                    "faces_blurred": privacy_result.faces_blurred,
                    "blur_method": privacy_result.blur_method,
                    "blur_kernel_size": privacy_result.blur_kernel_size,
                    "pii_detected": privacy_result.pii_detected
                },
                "evidence_frame_path": str(evidence_dir / evidence_filename),
                "frame_quality": {
                    "brightness": sampled_frame.quality.brightness,
                    "contrast": sampled_frame.quality.contrast,
                    "blur_score": sampled_frame.quality.blur_score,
                    "resolution": sampled_frame.quality.resolution
                },
                "edge_metrics": {
                    "inference_time_ms": round(proc_time, 1),
                    "model_used": "yolov8n",
                    "device": "CPU"
                }
            }
            
            all_telemetry.append(telemetry)
        
        # Build summary report
        avg_persons = float(np.mean(total_persons_detected)) if total_persons_detected else 0
        max_persons = int(np.max(total_persons_detected)) if total_persons_detected else 0
        min_persons = int(np.min(total_persons_detected)) if total_persons_detected else 0
        avg_proc_time = float(np.mean(processing_times)) if processing_times else 0
        
        report = {
            "pipeline_version": "0.1.0",
            "processing_timestamp": datetime.now(IST).strftime("%Y-%m-%dT%H:%M:%S+05:30"),
            "centre_id": self.centre_id,
            "camera_id": self.camera_id,
            "video_source": video_path,
            "summary": {
                "total_frames_sampled": frame_count,
                "sampling_interval_seconds": self.sampler.sampling_interval,
                "attendance": {
                    "average_detected": round(avg_persons, 1),
                    "max_detected": max_persons,
                    "min_detected": min_persons,
                    "per_frame_counts": total_persons_detected
                },
                "equipment": {
                    "unique_categories_detected": len(all_equipment),
                    "items": dict(all_equipment)
                },
                "performance": {
                    "avg_inference_time_ms": round(avg_proc_time, 1),
                    "total_processing_time_seconds": round(sum(processing_times) / 1000, 2)
                },
                "bandwidth": bandwidth
            },
            "telemetry_records": all_telemetry
        }
        
        # Save report
        report_path = output_dir / "telemetry_report.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n{'=' * 60}")
        print(f"  PIPELINE COMPLETE")
        print(f"{'=' * 60}")
        print(f"  Frames processed:  {frame_count}")
        print(f"  Avg persons:       {avg_persons:.1f}")
        print(f"  Max persons:       {max_persons}")
        print(f"  Equipment types:   {len(all_equipment)}")
        print(f"  Avg inference:     {avg_proc_time:.0f}ms")
        print(f"  Report saved:      {report_path}")
        print(f"  Evidence frames:   {evidence_dir}")
        print(f"  Annotated frames:  {annotated_dir}")
        print(f"{'=' * 60}")
        
        return report


# Backwards compatibility aliases
DrishtiPipeline = ParmanAIPipeline
DrishtiKushalPipeline = ParmanAIPipeline


def main():
    parser = argparse.ArgumentParser(
        description="Parman AI Engine - Training Centre Monitor"
    )
    parser.add_argument(
        "--video", "-v",
        type=str,
        required=True,
        help="Path to input video file"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default="output",
        help="Output directory (default: output/)"
    )
    parser.add_argument(
        "--interval", "-i",
        type=float,
        default=2.0,
        help="Sampling interval in seconds (default: 2.0, use 15-30 for production)"
    )
    parser.add_argument(
        "--max-frames", "-m",
        type=int,
        default=None,
        help="Maximum frames to process (default: all)"
    )
    parser.add_argument(
        "--confidence", "-c",
        type=float,
        default=0.35,
        help="Person detection confidence threshold (default: 0.35)"
    )
    parser.add_argument(
        "--centre-id",
        type=str,
        default="CTR-DL-001",
        help="Training centre ID (default: CTR-DL-001)"
    )
    parser.add_argument(
        "--camera-id",
        type=str,
        default="CAM-DL001-01",
        help="Camera ID (default: CAM-DL001-01)"
    )
    
    args = parser.parse_args()
    
    # Initialize pipeline
    pipeline = ParmanAIPipeline(
        sampling_interval=args.interval,
        person_confidence=args.confidence,
        device="cpu",
        centre_id=args.centre_id,
        camera_id=args.camera_id
    )
    
    # Process video
    report = pipeline.process_video(
        video_path=args.video,
        output_dir=args.output,
        max_frames=args.max_frames,
        save_evidence=True,
        save_annotated=True
    )
    
    return report


if __name__ == "__main__":
    main()
