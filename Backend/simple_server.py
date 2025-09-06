# TrackGuard AI Backend Service
# Simplified version using standard library to avoid dependency issues

import http.server
import socketserver
import json
import urllib.parse
import cgi
import tempfile
import os
import time
import threading
from pathlib import Path

class TrackGuardHandler(http.server.SimpleHTTPRequestHandler):
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_GET(self):
        """Handle GET requests"""
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            response = {
                "status": "healthy",
                "service": "trackguard-api",
                "timestamp": time.time()
            }
            self.wfile.write(json.dumps(response).encode())
            
        elif self.path == '/analytics/summary':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            response = {
                "total_videos_processed": 12,
                "total_detections": 45,
                "average_risk_score": 0.35,
                "alerts_today": 8,
                "system_uptime": time.time() - 3600  # 1 hour uptime
            }
            self.wfile.write(json.dumps(response).encode())
            
        elif self.path.startswith('/video/') and self.path.endswith('/results'):
            # Extract video_id from path
            video_id = self.path.split('/')[2]
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            # Mock detection results
            response = {
                "video_id": video_id,
                "status": "completed",
                "total_frames": 150,
                "processed_frames": 150,
                "detections": [
                    {
                        "frame_number": 45,
                        "timestamp": time.time() - 30,
                        "detections": [
                            {
                                "bbox": [100, 200, 300, 400],
                                "class": "person",
                                "confidence": 0.85,
                                "distance": 45.0,
                                "ttc": 2.1,
                                "risk_score": 0.75,
                                "decision": "CAUTION"
                            }
                        ],
                        "overall_decision": "CAUTION",
                        "overall_risk": 0.75,
                        "speed_kmph": 80.0,
                        "alerts": [
                            {
                                "type": "WARNING",
                                "message": "Person detected on track",
                                "timestamp": time.time() - 30
                            }
                        ]
                    }
                ]
            }
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_error(404, "Not found")
    
    def do_POST(self):
        """Handle POST requests"""
        
        if self.path == '/upload-video/':
            try:
                # Parse content length
                content_length = int(self.headers['Content-Length'])
                
                # Generate mock video ID
                video_id = f"video_{int(time.time())}"
                
                # Read and discard the body data
                self.rfile.read(content_length)
                
                # Send success response
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                
                response = {
                    "video_id": video_id,
                    "filename": "uploaded_video.mp4",
                    "status": "uploaded", 
                    "message": "Video uploaded successfully, processing started"
                }
                self.wfile.write(json.dumps(response).encode())
                
                # Start mock processing in background
                threading.Thread(target=self.simulate_processing, args=(video_id,)).start()
                
            except Exception as e:
                self.send_error(500, f"Upload failed: {str(e)}")
        else:
            self.send_error(404, "Not found")
    
    def simulate_processing(self, video_id):
        """Simulate video processing with realistic delays"""
        time.sleep(2)  # Simulate processing time
        print(f"Mock processing completed for video {video_id}")

# Create server
PORT = 8000
Handler = TrackGuardHandler

print(f"Starting TrackGuard AI Backend on port {PORT}")
print("Available endpoints:")
print("  GET  /health - Health check")
print("  GET  /analytics/summary - Analytics data")
print("  POST /upload-video/ - Upload video for processing")
print("  GET  /video/{id}/results - Get processing results")

try:
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"Server started at http://localhost:{PORT}")
        httpd.serve_forever()
except KeyboardInterrupt:
    print("\nShutting down server...")
except Exception as e:
    print(f"Server error: {e}")