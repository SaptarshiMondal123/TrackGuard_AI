from fastapi import FastAPI, File, UploadFile, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import os
import uuid
import json
import asyncio
import cv2
import numpy as np
from pathlib import Path
from typing import List, Dict, Any
import aiofiles
from ultralytics import YOLO
import time

# Import the existing detection logic
import sys
sys.path.append(os.path.dirname(__file__))

app = FastAPI(title="TrackGuard AI API", version="1.0.0")

# Enable CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create necessary directories
UPLOAD_DIR = "uploads"
RESULTS_DIR = "results"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)

# Mount static files
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")
app.mount("/results", StaticFiles(directory=RESULTS_DIR), name="results")

# Global variables for YOLO model and active connections
model = None
active_connections: List[WebSocket] = []

# Initialize the YOLO model
def initialize_model():
    global model
    try:
        # Try to load a local model first, fall back to downloading if needed
        model_path = "yolov8m.pt"  # Will download if not exists
        model = YOLO(model_path)
        print("YOLO model loaded successfully")
    except Exception as e:
        print(f"Error loading YOLO model: {e}")
        model = None

# Detection configuration (extracted from original file)
WHITELIST_CLASSES = {"person", "car", "truck", "motorcycle", "bicycle", "cow", "buffalo", "dog", "sheep", "goat", "elephant", "train", "animal"}
IGNORED_CLASSES = {"traffic light", "toothbrush", "surfboard", "snowboard", "boat", "banana", "bottle", "chair"}
MIN_CONF_DEFAULT = 0.40
MIN_BBOX_HEIGHT_PX = 30
MIN_BBOX_AREA_PX = 1500

CLASS_WEIGHT = {
    "person": 1.0, "car": 0.9, "truck": 1.1, "motorcycle": 0.95, "bicycle": 0.95,
    "cow": 1.2, "buffalo": 1.2, "dog": 1.1, "sheep": 1.15, "goat": 1.15,
    "elephant": 1.3, "train": 2.0, "animal": 1.3
}

def estimate_distance_from_bbox(bbox):
    """Estimate distance based on bounding box size"""
    x1, y1, x2, y2 = bbox
    height = y2 - y1
    # Simple inverse relationship - larger objects are closer
    K_CALIB = 4200.0
    return max(10.0, K_CALIB / max(height, 1))

def risk_score(distance, confidence, cls_name, speed_kmph):
    """Calculate risk score based on distance, confidence, class and speed"""
    base_weight = CLASS_WEIGHT.get(cls_name, 1.0)
    speed_factor = speed_kmph / 80.0  # Normalize to 80 km/h
    risk = (base_weight * confidence * speed_factor) / max(distance, 1.0)
    return min(1.0, risk * 100)

def ai_decision(distance, ttc, speed_kmph, cls_name):
    """AI decision making based on distance and time to collision"""
    if distance > 150.0:
        return "CLEAR"
    elif distance > 60.0:
        return "CAUTION" if ttc > 3.0 else "SLOW_DOWN"
    else:
        return "EMERGENCY_BRAKE"

def process_frame(frame):
    """Process a single frame and return detection results"""
    if model is None:
        return {"detections": [], "overall_risk": "UNKNOWN", "overall_decision": "NO_MODEL"}
    
    try:
        # Run inference
        results = model.predict(frame, imgsz=640, conf=MIN_CONF_DEFAULT, verbose=False, device='cpu')
        
        detections = []
        overall_risk = 0.0
        overall_decision = "CLEAR"
        
        for r in results:
            if r.boxes is not None and len(r.boxes) > 0:
                xyxy = r.boxes.xyxy.cpu().numpy()
                cls_ids = r.boxes.cls.cpu().numpy().astype(int)
                confs = r.boxes.conf.cpu().numpy()
                names = r.names

                for box, cid, conf in zip(xyxy, cls_ids, confs):
                    cls_name = names.get(int(cid), str(cid)).lower()
                    if cls_name in IGNORED_CLASSES or cls_name not in WHITELIST_CLASSES:
                        continue
                    if conf < MIN_CONF_DEFAULT:
                        continue

                    x1, y1, x2, y2 = box
                    bbox = [float(x1), float(y1), float(x2), float(y2)]
                    
                    # Filter by size
                    if (y2-y1) < MIN_BBOX_HEIGHT_PX or (x2-x1)*(y2-y1) < MIN_BBOX_AREA_PX:
                        continue
                    
                    # Estimate distance and risk
                    distance = estimate_distance_from_bbox(bbox)
                    speed_kmph = 80.0  # Simulated speed
                    ttc = distance / max(0.1, speed_kmph/3.6)
                    risk = risk_score(distance, conf, cls_name, speed_kmph)
                    decision = ai_decision(distance, ttc, speed_kmph, cls_name)
                    
                    detection = {
                        "bbox": bbox,
                        "class": cls_name,
                        "confidence": float(conf),
                        "distance": distance,
                        "risk_score": risk,
                        "decision": decision,
                        "ttc": ttc
                    }
                    detections.append(detection)
                    
                    # Update overall metrics
                    if risk > overall_risk:
                        overall_risk = risk
                        overall_decision = decision
        
        return {
            "detections": detections,
            "overall_risk": overall_risk,
            "overall_decision": overall_decision,
            "timestamp": time.time()
        }
    except Exception as e:
        print(f"Error processing frame: {e}")
        return {"detections": [], "overall_risk": 0.0, "overall_decision": "ERROR"}

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                # Connection closed, remove it
                self.active_connections.remove(connection)

manager = ConnectionManager()

@app.on_event("startup")
async def startup_event():
    """Initialize the application"""
    initialize_model()

@app.get("/")
async def root():
    return {"message": "TrackGuard AI API is running"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "model_loaded": model is not None,
        "timestamp": time.time()
    }

@app.post("/api/ai/upload")
async def upload_video(file: UploadFile = File(...)):
    """Upload and process a video file"""
    if not file.content_type.startswith('video/'):
        raise HTTPException(status_code=400, detail="File must be a video")
    
    # Generate unique filename
    file_id = str(uuid.uuid4())
    file_extension = Path(file.filename).suffix
    filename = f"{file_id}{file_extension}"
    file_path = Path(UPLOAD_DIR) / filename
    
    try:
        # Save uploaded file
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        return {
            "file_id": file_id,
            "filename": filename,
            "status": "uploaded",
            "message": "Video uploaded successfully. Use /api/ai/process to analyze."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")

@app.get("/api/ai/process/{file_id}")
async def process_video(file_id: str):
    """Process an uploaded video and return detection results"""
    try:
        # Find the video file
        video_path = None
        for ext in ['.mp4', '.avi', '.mov', '.mkv']:
            potential_path = Path(UPLOAD_DIR) / f"{file_id}{ext}"
            if potential_path.exists():
                video_path = potential_path
                break
        
        if not video_path:
            raise HTTPException(status_code=404, detail="Video file not found")
        
        # Process video
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise HTTPException(status_code=400, detail="Cannot open video file")
        
        # Process first few frames as sample
        results = []
        frame_count = 0
        max_frames = 30  # Limit processing for demo
        
        while frame_count < max_frames:
            ret, frame = cap.read()
            if not ret:
                break
            
            if frame_count % 5 == 0:  # Process every 5th frame
                result = process_frame(frame)
                result["frame_number"] = frame_count
                results.append(result)
            
            frame_count += 1
        
        cap.release()
        
        # Save results
        results_file = Path(RESULTS_DIR) / f"{file_id}_results.json"
        async with aiofiles.open(results_file, 'w') as f:
            await f.write(json.dumps(results, indent=2))
        
        return {
            "file_id": file_id,
            "total_frames": frame_count,
            "processed_frames": len(results),
            "results": results[:5],  # Return first 5 results
            "results_file": f"/results/{file_id}_results.json"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing video: {str(e)}")

@app.websocket("/api/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time communication"""
    await manager.connect(websocket)
    try:
        while True:
            # Wait for messages from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "ping":
                await websocket.send_text(json.dumps({
                    "type": "pong",
                    "timestamp": time.time()
                }))
            elif message.get("type") == "get_status":
                await websocket.send_text(json.dumps({
                    "type": "status",
                    "model_loaded": model is not None,
                    "timestamp": time.time()
                }))
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.get("/api/ai/results/{file_id}")
async def get_results(file_id: str):
    """Get processing results for a video"""
    results_file = Path(RESULTS_DIR) / f"{file_id}_results.json"
    
    if not results_file.exists():
        raise HTTPException(status_code=404, detail="Results not found")
    
    async with aiofiles.open(results_file, 'r') as f:
        content = await f.read()
        results = json.loads(content)
    
    return {
        "file_id": file_id,
        "results": results
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)