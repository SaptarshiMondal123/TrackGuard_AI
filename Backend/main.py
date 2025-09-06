from fastapi import FastAPI, File, UploadFile, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import asyncio
import json
import os
import cv2
import time
import uuid
from pathlib import Path
from typing import List, Dict, Any
import aiofiles
from pydantic import BaseModel

# Import existing detection system
from detection_service import YOLODetectionService

app = FastAPI(title="TrackGuard AI API", version="1.0.0")

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize detection service
detection_service = YOLODetectionService()

# Create directories
os.makedirs("uploads", exist_ok=True)
os.makedirs("outputs", exist_ok=True)
os.makedirs("static", exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/outputs", StaticFiles(directory="outputs"), name="outputs")

# Pydantic models
class DetectionResult(BaseModel):
    frame_number: int
    timestamp: float
    detections: List[Dict[str, Any]]
    overall_decision: str
    overall_risk: float
    speed_kmph: float
    alerts: List[Dict[str, Any]]

class ProcessingStatus(BaseModel):
    status: str  # "processing", "completed", "error"
    progress: float
    message: str
    video_id: str

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                await self.disconnect(connection)

manager = ConnectionManager()

@app.get("/")
async def root():
    return {"message": "TrackGuard AI Backend API", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "trackguard-api"}

@app.post("/upload-video/")
async def upload_video(file: UploadFile = File(...)):
    """Upload video for AI processing"""
    if not file.content_type.startswith('video/'):
        raise HTTPException(status_code=400, detail="File must be a video")
    
    # Generate unique filename
    video_id = str(uuid.uuid4())
    filename = f"{video_id}_{file.filename}"
    file_path = f"uploads/{filename}"
    
    # Save uploaded file
    async with aiofiles.open(file_path, 'wb') as f:
        content = await file.read()
        await f.write(content)
    
    # Start processing asynchronously
    asyncio.create_task(process_video_async(video_id, file_path))
    
    return {
        "video_id": video_id,
        "filename": filename,
        "status": "uploaded",
        "message": "Video uploaded successfully, processing started"
    }

async def process_video_async(video_id: str, file_path: str):
    """Process video asynchronously and send updates via WebSocket"""
    try:
        await manager.broadcast(json.dumps({
            "type": "status_update",
            "video_id": video_id,
            "status": "processing",
            "progress": 0,
            "message": "Starting AI analysis..."
        }))
        
        # Process video using existing detection service
        async for result in detection_service.process_video_stream(file_path, video_id):
            # Broadcast real-time results
            await manager.broadcast(json.dumps({
                "type": "detection_result",
                "video_id": video_id,
                **result
            }))
        
        await manager.broadcast(json.dumps({
            "type": "status_update",
            "video_id": video_id,
            "status": "completed",
            "progress": 100,
            "message": "Processing completed successfully"
        }))
        
    except Exception as e:
        await manager.broadcast(json.dumps({
            "type": "status_update",
            "video_id": video_id,
            "status": "error",
            "progress": 0,
            "message": f"Processing failed: {str(e)}"
        }))

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time communication"""
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Handle incoming WebSocket messages if needed
            message = json.loads(data)
            if message.get("type") == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.get("/analytics/summary")
async def get_analytics_summary():
    """Get analytics summary"""
    # This would normally query a database
    return {
        "total_videos_processed": 0,
        "total_detections": 0,
        "average_risk_score": 0.0,
        "alerts_today": 0,
        "system_uptime": time.time()
    }

@app.get("/video/{video_id}/results")
async def get_video_results(video_id: str):
    """Get processing results for a video"""
    results_file = f"outputs/{video_id}_results.json"
    if os.path.exists(results_file):
        with open(results_file, 'r') as f:
            return json.load(f)
    else:
        raise HTTPException(status_code=404, detail="Results not found")

@app.get("/video/{video_id}/output")
async def get_processed_video(video_id: str):
    """Get processed video file"""
    output_file = f"outputs/{video_id}_processed.mp4"
    if os.path.exists(output_file):
        return FileResponse(output_file, media_type="video/mp4")
    else:
        raise HTTPException(status_code=404, detail="Processed video not found")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)