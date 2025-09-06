#!/usr/bin/env python3
"""
Simplified FastAPI server for TrackGuard AI
This version provides the API structure without heavy ML dependencies
"""
import os
import json
import uuid
import time
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional

# Check if required packages are available
try:
    from fastapi import FastAPI, File, UploadFile, WebSocket, WebSocketDisconnect, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import JSONResponse
    fastapi_available = True
except ImportError:
    fastapi_available = False

# Simple mock detection system when full dependencies aren't available
class MockDetectionSystem:
    """Mock detection system for demonstration purposes"""
    
    def __init__(self):
        self.model_loaded = True
    
    def process_frame_mock(self, frame_number: int = 0) -> Dict[str, Any]:
        """Generate mock detection results"""
        import random
        
        # Generate some random mock detections
        detections = []
        num_detections = random.randint(0, 3)
        
        for i in range(num_detections):
            # Mock bounding box
            x1, y1 = random.randint(50, 200), random.randint(50, 200)
            x2, y2 = x1 + random.randint(50, 150), y1 + random.randint(50, 150)
            
            # Mock object classes
            classes = ["person", "car", "truck", "bicycle", "animal"]
            cls_name = random.choice(classes)
            
            # Mock confidence and risk
            confidence = random.uniform(0.5, 0.95)
            distance = random.uniform(20, 200)
            risk_score = random.uniform(0.1, 0.9)
            
            # Mock decision based on risk
            if risk_score > 0.7:
                decision = "EMERGENCY_BRAKE"
            elif risk_score > 0.4:
                decision = "SLOW_DOWN"
            elif risk_score > 0.2:
                decision = "CAUTION"
            else:
                decision = "CLEAR"
            
            detection = {
                "bbox": [x1, y1, x2, y2],
                "class": cls_name,
                "confidence": confidence,
                "distance": distance,
                "risk_score": risk_score,
                "decision": decision,
                "ttc": distance / max(22.2, 0.1)  # time to collision at 80km/h
            }
            detections.append(detection)
        
        # Overall assessment
        if detections:
            overall_risk = max(d["risk_score"] for d in detections)
            overall_decision = min([d["decision"] for d in detections], 
                                 key=lambda x: ["CLEAR", "CAUTION", "SLOW_DOWN", "EMERGENCY_BRAKE"].index(x))
        else:
            overall_risk = 0.0
            overall_decision = "CLEAR"
        
        return {
            "detections": detections,
            "overall_risk": overall_risk,
            "overall_decision": overall_decision,
            "timestamp": time.time(),
            "frame_number": frame_number
        }

# Initialize the detection system
detection_system = MockDetectionSystem()

if fastapi_available:
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
            for connection in self.active_connections[:]:  # Use slice to avoid modification during iteration
                try:
                    await connection.send_text(message)
                except:
                    # Connection closed, remove it
                    self.active_connections.remove(connection)

    manager = ConnectionManager()

    @app.get("/")
    async def root():
        return {"message": "TrackGuard AI API is running", "version": "1.0.0"}

    @app.get("/health")
    async def health_check():
        return {
            "status": "healthy",
            "model_loaded": detection_system.model_loaded,
            "timestamp": time.time(),
            "api_version": "1.0.0"
        }

    @app.post("/api/ai/upload")
    async def upload_video(file: UploadFile = File(...)):
        """Upload and process a video file"""
        if not file.content_type or not file.content_type.startswith('video/'):
            raise HTTPException(status_code=400, detail="File must be a video")
        
        # Generate unique filename
        file_id = str(uuid.uuid4())
        file_extension = Path(file.filename or "video.mp4").suffix or ".mp4"
        filename = f"{file_id}{file_extension}"
        file_path = Path(UPLOAD_DIR) / filename
        
        try:
            # Save uploaded file
            content = await file.read()
            with open(file_path, 'wb') as f:
                f.write(content)
            
            return {
                "file_id": file_id,
                "filename": filename,
                "status": "uploaded",
                "size": len(content),
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
            
            # Generate mock processing results
            results = []
            total_frames = 150  # Mock total frames
            processed_frames = 30  # Process every 5th frame
            
            for i in range(0, processed_frames):
                frame_num = i * 5
                result = detection_system.process_frame_mock(frame_num)
                results.append(result)
            
            # Save results
            results_file = Path(RESULTS_DIR) / f"{file_id}_results.json"
            with open(results_file, 'w') as f:
                json.dump(results, f, indent=2)
            
            return {
                "file_id": file_id,
                "status": "processed",
                "total_frames": total_frames,
                "processed_frames": len(results),
                "results": results[:5],  # Return first 5 results for preview
                "results_file": f"/results/{file_id}_results.json"
            }
        
        except HTTPException:
            raise
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
                        "model_loaded": detection_system.model_loaded,
                        "timestamp": time.time()
                    }))
                elif message.get("type") == "start_live_demo":
                    # Send a series of mock live detections
                    for i in range(10):
                        result = detection_system.process_frame_mock(i)
                        result["type"] = "live_detection"
                        await websocket.send_text(json.dumps(result))
                        await asyncio.sleep(0.5)  # Simulate real-time processing
        except WebSocketDisconnect:
            manager.disconnect(websocket)
        except Exception as e:
            print(f"WebSocket error: {e}")
            manager.disconnect(websocket)

    @app.get("/api/ai/results/{file_id}")
    async def get_results(file_id: str):
        """Get processing results for a video"""
        results_file = Path(RESULTS_DIR) / f"{file_id}_results.json"
        
        if not results_file.exists():
            raise HTTPException(status_code=404, detail="Results not found")
        
        with open(results_file, 'r') as f:
            results = json.load(f)
        
        return {
            "file_id": file_id,
            "results": results
        }

    @app.get("/api/alerts")
    async def get_alerts():
        """Get active alerts"""
        # Mock alerts for demonstration
        alerts = [
            {
                "id": "alert_1",
                "type": "WARNING",
                "message": "Person detected on track at 150m",
                "timestamp": time.time() - 30,
                "status": "active",
                "location": {"lat": 22.5726, "lng": 88.3639}
            },
            {
                "id": "alert_2", 
                "type": "INFO",
                "message": "Vehicle cleared from track section",
                "timestamp": time.time() - 120,
                "status": "acknowledged",
                "location": {"lat": 22.5742, "lng": 88.3658}
            }
        ]
        return {"alerts": alerts}

    @app.post("/api/alerts/{alert_id}/acknowledge")
    async def acknowledge_alert(alert_id: str):
        """Acknowledge an alert"""
        return {
            "alert_id": alert_id,
            "status": "acknowledged",
            "timestamp": time.time()
        }

    if __name__ == "__main__":
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=8000)

else:
    # Fallback when FastAPI is not available
    print("FastAPI not available. Please install required dependencies:")
    print("pip install fastapi uvicorn python-multipart")
    
    # Simple HTTP server fallback
    import http.server
    import socketserver
    from urllib.parse import urlparse, parse_qs
    import threading
    
    class SimpleAPIHandler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == '/':
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                response = {"message": "TrackGuard AI API is running (simple mode)", "version": "1.0.0"}
                self.wfile.write(json.dumps(response).encode())
            elif self.path == '/health':
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                response = {
                    "status": "healthy",
                    "model_loaded": False,
                    "timestamp": time.time(),
                    "mode": "simple"
                }
                self.wfile.write(json.dumps(response).encode())
            else:
                self.send_response(404)
                self.end_headers()
        
        def do_OPTIONS(self):
            self.send_response(200)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()
    
    def run_simple_server():
        PORT = 8000
        with socketserver.TCPServer(("", PORT), SimpleAPIHandler) as httpd:
            print(f"Simple API server running at http://localhost:{PORT}")
            httpd.serve_forever()
    
    if __name__ == "__main__":
        run_simple_server()