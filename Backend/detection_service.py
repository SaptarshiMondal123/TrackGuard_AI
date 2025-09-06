import cv2
import time
import os
import math
import uuid
import json
import numpy as np
import pandas as pd
from pathlib import Path
from ultralytics import YOLO
import asyncio
from typing import AsyncGenerator, Dict, Any, List

class YOLODetectionService:
    def __init__(self):
        # Use a publicly available YOLO model
        self.model_path = "yolov8n.pt"  # This will download automatically
        self.model = None
        self.load_model()
        
        # Configuration from original file
        self.FRAME_SKIP = 2
        self.BATCH_SIZE = 6
        self.IMG_SIZE = 640
        
        # Risk assessment parameters
        self.K_CALIB = 4200.0
        self.REACTION_TIME = 1.0
        self.DECEL = 1.2
        self.WARNING_DIST = 150.0
        self.BRAKE_DIST = 60.0
        self.PERSISTENCE_FRAMES = 3
        self.FORGET_FRAMES = 12
        
        # Class weights and filtering
        self.CLASS_WEIGHT = {
            "person": 1.0, "car": 0.9, "truck": 1.1, "motorcycle": 0.95, "bicycle": 0.95,
            "cow": 1.2, "buffalo": 1.2, "dog": 1.1, "sheep": 1.15, "goat": 1.15,
            "elephant": 1.3, "train": 2.0, "animal": 1.3
        }
        
        self.WHITELIST_CLASSES = set(self.CLASS_WEIGHT.keys())
        self.IGNORED_CLASSES = {"traffic light", "toothbrush", "surfboard", "snowboard", "boat", "banana", "bottle", "chair"}
        self.MIN_CONF_DEFAULT = 0.40
        self.MIN_BBOX_HEIGHT_PX = 30
        self.MIN_BBOX_AREA_PX = 1500
        self.ROI_CENTER_X_RATIO = (0.20, 0.80)
        self.ROI_MIN_BOTTOM_RATIO = 0.40
        
        # GPS route (simulated)
        self.TRAIN_ROUTE = [
            (22.5726, 88.3639), (22.5742, 88.3658), (22.5760, 88.3676),
            (22.5775, 88.3695), (22.5790, 88.3714), (22.5805, 88.3733)
        ]
        
        self.persistence = {}
        
    def load_model(self):
        """Load YOLO model"""
        try:
            self.model = YOLO(self.model_path)
            print(f"YOLO model loaded successfully: {self.model_path}")
        except Exception as e:
            print(f"Error loading model: {e}")
            # Fallback to nano model
            self.model = YOLO("yolov8n.pt")
            
    def center_of_bbox(self, bbox):
        """Get center point of bounding box"""
        x1, y1, x2, y2 = bbox
        return ((x1 + x2) / 2, (y1 + y2) / 2)
    
    def bbox_area(self, bbox):
        """Calculate bounding box area"""
        x1, y1, x2, y2 = bbox
        return (x2 - x1) * (y2 - y1)
    
    def estimate_distance_from_bbox(self, bbox):
        """Estimate distance based on bounding box size"""
        _, _, _, y2 = bbox
        return max(10.0, self.K_CALIB / max(1, y2))
    
    def is_in_rail_roi(self, bbox, frame_shape):
        """Check if bounding box is in rail region of interest"""
        h, w = frame_shape[:2]
        cx, cy = self.center_of_bbox(bbox)
        
        if not (self.ROI_CENTER_X_RATIO[0] * w <= cx <= self.ROI_CENTER_X_RATIO[1] * w):
            return False
        
        _, _, _, y2 = bbox
        if (y2 / h) < self.ROI_MIN_BOTTOM_RATIO:
            return False
            
        return True
    
    def risk_score(self, distance, confidence, class_name, speed_kmph):
        """Calculate risk score"""
        weight = self.CLASS_WEIGHT.get(class_name, 1.0)
        base_risk = (weight * confidence) / max(0.1, distance / 100.0)
        
        if distance < self.BRAKE_DIST:
            return min(1.0, base_risk * 2.0)
        elif distance < self.WARNING_DIST:
            return min(0.8, base_risk * 1.5)
        else:
            return min(0.5, base_risk)
    
    def ai_decision(self, distance, ttc, speed_kmph, class_name):
        """AI decision making"""
        if distance < self.BRAKE_DIST or ttc < 3.0:
            return "EMERGENCY_BRAKE"
        elif distance < self.WARNING_DIST or ttc < 6.0:
            return "CAUTION"
        elif distance < 200.0:
            return "SLOW_DOWN"
        else:
            return "CLEAR"
    
    async def process_video_stream(self, video_path: str, video_id: str) -> AsyncGenerator[Dict[str, Any], None]:
        """Process video and yield real-time results"""
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError("Cannot open video file")
        
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        frame_count = 0
        batch_frames = []
        batch_orig = []
        
        # Simulated speed
        SIM_SPEED_KMPH = 80.0
        
        # Output video writer
        out_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        out_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        out_fps = max(10, int(fps or 20))
        output_path = f"outputs/{video_id}_processed.mp4"
        
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out_writer = cv2.VideoWriter(output_path, fourcc, out_fps, (out_w, out_h))
        
        all_results = []
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                frame_count += 1
                
                if frame_count % self.FRAME_SKIP != 0:
                    out_writer.write(frame)  # Write original frame
                    continue
                
                h, w = frame.shape[:2]
                resized = cv2.resize(frame, (self.IMG_SIZE, self.IMG_SIZE))
                batch_frames.append(resized)
                batch_orig.append(frame.copy())
                
                if len(batch_frames) >= self.BATCH_SIZE or frame_count == total_frames:
                    # Process batch
                    results = self.model.predict(batch_frames, imgsz=self.IMG_SIZE, conf=0.30, verbose=False)
                    
                    for idx, r in enumerate(results):
                        orig_frame = batch_orig[idx]
                        scale_x = orig_frame.shape[1] / self.IMG_SIZE
                        scale_y = orig_frame.shape[0] / self.IMG_SIZE
                        
                        detections = []
                        draw_frame = orig_frame.copy()
                        
                        if r.boxes is not None and len(r.boxes) > 0:
                            xyxy = r.boxes.xyxy.cpu().numpy()
                            cls_ids = r.boxes.cls.cpu().numpy().astype(int)
                            confs = r.boxes.conf.cpu().numpy()
                            names = r.names
                            
                            for box, cid, conf in zip(xyxy, cls_ids, confs):
                                cls_name = names.get(int(cid), str(cid)).lower()
                                
                                if cls_name in self.IGNORED_CLASSES:
                                    continue
                                if conf < self.MIN_CONF_DEFAULT:
                                    continue
                                
                                # Scale bounding box back to original size
                                x1, y1, x2, y2 = box
                                x1 *= scale_x
                                x2 *= scale_x  
                                y1 *= scale_y
                                y2 *= scale_y
                                bbox = [x1, y1, x2, y2]
                                
                                if (y2-y1) < self.MIN_BBOX_HEIGHT_PX or self.bbox_area(bbox) < self.MIN_BBOX_AREA_PX:
                                    continue
                                if not self.is_in_rail_roi(bbox, orig_frame.shape):
                                    continue
                                
                                # Calculate metrics
                                dist = self.estimate_distance_from_bbox(bbox)
                                ttc = dist / max(0.1, SIM_SPEED_KMPH/3.6)
                                score = self.risk_score(dist, conf, cls_name, SIM_SPEED_KMPH)
                                decision = self.ai_decision(dist, ttc, SIM_SPEED_KMPH, cls_name)
                                
                                # Draw bounding box
                                x1, y1, x2, y2 = map(int, bbox)
                                color = (0, 255, 0) if decision == "CLEAR" else \
                                       (0, 165, 255) if decision in ["SLOW_DOWN", "CAUTION"] else \
                                       (0, 0, 255)
                                
                                cv2.rectangle(draw_frame, (x1, y1), (x2, y2), color, 2)
                                cv2.putText(draw_frame, f"{cls_name} {conf:.2f} {decision}", 
                                          (x1, max(20, y1-5)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                                
                                detection = {
                                    "bbox": [x1, y1, x2, y2],
                                    "class": cls_name,
                                    "confidence": float(conf),
                                    "distance": float(dist),
                                    "ttc": float(ttc),
                                    "risk_score": float(score),
                                    "decision": decision
                                }
                                detections.append(detection)
                        
                        # Calculate overall metrics
                        overall_risk = max([d["risk_score"] for d in detections], default=0.0)
                        overall_decision = "CLEAR"
                        if any(d["decision"] == "EMERGENCY_BRAKE" for d in detections):
                            overall_decision = "EMERGENCY_BRAKE"
                        elif any(d["decision"] == "CAUTION" for d in detections):
                            overall_decision = "CAUTION"
                        elif any(d["decision"] == "SLOW_DOWN" for d in detections):
                            overall_decision = "SLOW_DOWN"
                        
                        # Write processed frame
                        out_writer.write(draw_frame)
                        
                        # Create result
                        result = {
                            "frame_number": frame_count - self.BATCH_SIZE + idx + 1,
                            "timestamp": time.time(),
                            "detections": detections,
                            "overall_decision": overall_decision,
                            "overall_risk": overall_risk,
                            "speed_kmph": SIM_SPEED_KMPH,
                            "progress": (frame_count / total_frames) * 100,
                            "alerts": []
                        }
                        
                        # Add alerts for high-risk situations
                        if overall_risk > 0.7:
                            result["alerts"].append({
                                "type": "CRITICAL" if overall_risk > 0.9 else "WARNING",
                                "message": f"High risk detected: {overall_decision}",
                                "timestamp": time.time()
                            })
                        
                        all_results.append(result)
                        yield result
                    
                    # Clear batch
                    batch_frames = []
                    batch_orig = []
                
                # Small delay to prevent overwhelming
                await asyncio.sleep(0.01)
        
        finally:
            cap.release()
            out_writer.release()
            
            # Save results to file
            results_path = f"outputs/{video_id}_results.json"
            with open(results_path, 'w') as f:
                json.dump(all_results, f, indent=2)