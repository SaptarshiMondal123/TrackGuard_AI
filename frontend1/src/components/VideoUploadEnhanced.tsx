import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Upload, Play, X, AlertTriangle, CheckCircle, Clock, Loader2, Eye, Zap } from 'lucide-react';

// Detection result types
interface Detection {
  bbox: [number, number, number, number];
  class: string;
  confidence: number;
  distance: number;
  risk_score: number;
  decision: string;
  ttc: number;
}

interface DetectionResult {
  detections: Detection[];
  overall_risk: number;
  overall_decision: string;
  timestamp: number;
  frame_number?: number;
}

interface UploadResponse {
  file_id: string;
  filename: string;
  status: string;
  size?: number;
  message: string;
}

interface ProcessResponse {
  file_id: string;
  status: string;
  total_frames: number;
  processed_frames: number;
  results: DetectionResult[];
  results_file: string;
}

// Configuration
const API_BASE_URL = 'http://localhost:8000';

const VideoUpload = () => {
  const [uploadedVideo, setUploadedVideo] = useState<string | null>(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [currentFile, setCurrentFile] = useState<File | null>(null);
  const [fileId, setFileId] = useState<string | null>(null);
  const [detectionResults, setDetectionResults] = useState<DetectionResult[]>([]);
  const [currentFrame, setCurrentFrame] = useState(0);
  const [showDetections, setShowDetections] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<'disconnected' | 'connecting' | 'connected'>('disconnected');
  
  const fileInputRef = useRef<HTMLInputElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const wsRef = useRef<WebSocket | null>(null);

  // Check API health on mount
  useEffect(() => {
    checkAPIHealth();
  }, []);

  const checkAPIHealth = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/health`);
      if (response.ok) {
        setConnectionStatus('connected');
      } else {
        setConnectionStatus('disconnected');
      }
    } catch (error) {
      console.log('API not available:', error);
      setConnectionStatus('disconnected');
    }
  };

  // Initialize WebSocket connection
  const initWebSocket = useCallback(() => {
    if (connectionStatus !== 'connected') return;
    
    try {
      const ws = new WebSocket(`ws://localhost:8000/api/ws`);
      
      ws.onopen = () => {
        console.log('WebSocket connected');
        ws.send(JSON.stringify({ type: 'get_status' }));
      };
      
      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'live_detection') {
          // Handle real-time detection updates
          setDetectionResults(prev => [...prev.slice(-10), data]); // Keep last 10 results
        }
      };
      
      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
      
      ws.onclose = () => {
        console.log('WebSocket disconnected');
      };
      
      wsRef.current = ws;
    } catch (error) {
      console.error('Failed to initialize WebSocket:', error);
    }
  }, [connectionStatus]);

  useEffect(() => {
    initWebSocket();
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [initWebSocket]);

  const uploadToAPI = async (file: File): Promise<UploadResponse | null> => {
    if (connectionStatus !== 'connected') return null;
    
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(`${API_BASE_URL}/api/ai/upload`, {
        method: 'POST',
        body: formData,
      });

      if (response.ok) {
        return await response.json();
      } else {
        throw new Error('Upload failed');
      }
    } catch (error) {
      console.error('Upload error:', error);
      return null;
    }
  };

  const processVideo = async (fileId: string): Promise<ProcessResponse | null> => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/ai/process/${fileId}`);
      
      if (response.ok) {
        return await response.json();
      } else {
        throw new Error('Processing failed');
      }
    } catch (error) {
      console.error('Processing error:', error);
      return null;
    }
  };

  const handleFileSelect = async (file: File) => {
    if (file.type.startsWith('video/')) {
      setCurrentFile(file);
      const url = URL.createObjectURL(file);
      setUploadedVideo(url);
      
      // Upload to API if connected
      if (connectionStatus === 'connected') {
        setIsUploading(true);
        setUploadProgress(0);
        
        // Simulate upload progress
        const progressInterval = setInterval(() => {
          setUploadProgress(prev => Math.min(prev + 10, 90));
        }, 100);
        
        const uploadResult = await uploadToAPI(file);
        clearInterval(progressInterval);
        setUploadProgress(100);
        
        if (uploadResult) {
          setFileId(uploadResult.file_id);
          setIsUploading(false);
          
          // Start processing
          setIsProcessing(true);
          const processResult = await processVideo(uploadResult.file_id);
          
          if (processResult) {
            setDetectionResults(processResult.results || []);
            setShowDetections(true);
          }
          setIsProcessing(false);
        } else {
          setIsUploading(false);
          // Show mock results for demo
          generateMockResults();
        }
      } else {
        // Show mock results when API is not available
        generateMockResults();
      }
    }
  };

  const generateMockResults = () => {
    const mockResults: DetectionResult[] = [];
    for (let i = 0; i < 5; i++) {
      mockResults.push({
        detections: [
          {
            bbox: [100 + i * 20, 150 + i * 10, 200 + i * 20, 250 + i * 10],
            class: ['person', 'car', 'truck'][i % 3],
            confidence: 0.7 + Math.random() * 0.25,
            distance: 50 + Math.random() * 100,
            risk_score: Math.random() * 0.8,
            decision: ['CLEAR', 'CAUTION', 'SLOW_DOWN'][i % 3],
            ttc: 2 + Math.random() * 8
          }
        ],
        overall_risk: Math.random() * 0.8,
        overall_decision: ['CLEAR', 'CAUTION', 'SLOW_DOWN'][i % 3],
        timestamp: Date.now(),
        frame_number: i * 30
      });
    }
    setDetectionResults(mockResults);
    setShowDetections(true);
  };

  const drawDetections = useCallback(() => {
    if (!canvasRef.current || !videoRef.current || !showDetections) return;
    
    const canvas = canvasRef.current;
    const video = videoRef.current;
    const ctx = canvas.getContext('2d');
    
    if (!ctx) return;
    
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    const currentResult = detectionResults[Math.floor(currentFrame / 30)] || detectionResults[0];
    if (!currentResult) return;
    
    currentResult.detections.forEach((detection) => {
      const [x1, y1, x2, y2] = detection.bbox;
      
      // Color based on decision
      let color = '#10B981'; // Green for CLEAR
      if (detection.decision === 'CAUTION') color = '#F59E0B'; // Amber
      if (detection.decision === 'SLOW_DOWN') color = '#EF4444'; // Red
      if (detection.decision === 'EMERGENCY_BRAKE') color = '#DC2626'; // Dark red
      
      // Draw bounding box
      ctx.strokeStyle = color;
      ctx.lineWidth = 3;
      ctx.strokeRect(x1, y1, x2 - x1, y2 - y1);
      
      // Draw label background
      const labelText = `${detection.class} ${(detection.confidence * 100).toFixed(0)}% - ${detection.decision}`;
      const metrics = ctx.measureText(labelText);
      const labelHeight = 20;
      
      ctx.fillStyle = color;
      ctx.fillRect(x1, y1 - labelHeight, metrics.width + 10, labelHeight);
      
      // Draw label text
      ctx.fillStyle = 'white';
      ctx.font = '14px Arial';
      ctx.fillText(labelText, x1 + 5, y1 - 5);
      
      // Draw risk indicator
      if (detection.risk_score > 0.5) {
        ctx.beginPath();
        ctx.arc(x2 - 15, y1 + 15, 8, 0, 2 * Math.PI);
        ctx.fillStyle = detection.risk_score > 0.7 ? '#DC2626' : '#F59E0B';
        ctx.fill();
        ctx.fillStyle = 'white';
        ctx.font = '10px Arial';
        ctx.fillText('!', x2 - 18, y1 + 19);
      }
    });
  }, [detectionResults, currentFrame, showDetections]);

  // Update canvas when video time changes
  useEffect(() => {
    if (videoRef.current) {
      const video = videoRef.current;
      const handleTimeUpdate = () => {
        setCurrentFrame(Math.floor(video.currentTime * 30)); // Assume 30fps
        drawDetections();
      };
      
      video.addEventListener('timeupdate', handleTimeUpdate);
      return () => video.removeEventListener('timeupdate', handleTimeUpdate);
    }
  }, [drawDetections]);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      handleFileSelect(files[0]);
    }
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      handleFileSelect(files[0]);
    }
  };

  const clearVideo = () => {
    if (uploadedVideo) {
      URL.revokeObjectURL(uploadedVideo);
    }
    setUploadedVideo(null);
    setCurrentFile(null);
    setFileId(null);
    setDetectionResults([]);
    setShowDetections(false);
    setUploadProgress(0);
    setCurrentFrame(0);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const getRiskColor = (risk: number) => {
    if (risk > 0.7) return 'text-red-400';
    if (risk > 0.4) return 'text-amber-400';
    return 'text-green-400';
  };

  const getStatusIcon = () => {
    if (connectionStatus === 'connected') {
      return <CheckCircle className="w-4 h-4 text-green-400" />;
    } else if (connectionStatus === 'connecting') {
      return <Clock className="w-4 h-4 text-amber-400" />;
    } else {
      return <AlertTriangle className="w-4 h-4 text-red-400" />;
    }
  };

  return (
    <section id="demo" className="py-20 bg-gradient-to-b from-black to-gray-900">
      <div className="container mx-auto px-6">
        <div className="text-center mb-12">
          <h2 className="text-4xl md:text-5xl font-bold text-white mb-4">
            See TrackGuard in <span className="text-green-400">Action</span>
          </h2>
          <p className="text-gray-300 text-xl max-w-2xl mx-auto mb-4">
            Upload a railway video to experience our AI-powered collision detection system
          </p>
          
          {/* API Status */}
          <div className="flex items-center justify-center space-x-2 text-sm">
            {getStatusIcon()}
            <span className={`font-medium ${
              connectionStatus === 'connected' ? 'text-green-400' : 
              connectionStatus === 'connecting' ? 'text-amber-400' : 'text-red-400'
            }`}>
              API {connectionStatus === 'connected' ? 'Connected' : connectionStatus === 'connecting' ? 'Connecting...' : 'Demo Mode'}
            </span>
          </div>
        </div>

        <div className="max-w-4xl mx-auto">
          {!uploadedVideo ? (
            <div
              className={`
                relative border-2 border-dashed rounded-2xl p-12 text-center cursor-pointer
                transition-all duration-300 transform hover:scale-[1.02]
                ${isDragOver 
                  ? 'border-green-400 bg-green-400/5 shadow-lg shadow-green-400/20' 
                  : 'border-gray-600 hover:border-green-400 hover:bg-green-400/5'
                }
              `}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
            >
              <div className="flex flex-col items-center space-y-6">
                <div className={`
                  p-6 rounded-full transition-all duration-300
                  ${isDragOver ? 'bg-green-400/20 scale-110' : 'bg-gray-800'}
                `}>
                  <Upload className={`w-12 h-12 ${isDragOver ? 'text-green-400' : 'text-gray-400'}`} />
                </div>
                
                <div>
                  <h3 className="text-2xl font-bold text-white mb-2">
                    Upload Rail Video to See TrackGuard in Action
                  </h3>
                  <p className="text-gray-400 mb-6">
                    Drag and drop your video here, or click to browse
                  </p>
                  <div className="inline-flex px-6 py-3 bg-gradient-to-r from-green-500 to-emerald-600 text-white rounded-lg font-semibold hover:from-green-600 hover:to-emerald-700 transition-all">
                    Choose Video File
                  </div>
                </div>
              </div>
              
              <input
                ref={fileInputRef}
                type="file"
                accept="video/*"
                onChange={handleFileInputChange}
                className="hidden"
              />
            </div>
          ) : (
            <div className="bg-gray-900 rounded-2xl p-6 border border-gray-700 shadow-2xl">
              <div className="flex justify-between items-center mb-4">
                <div className="flex items-center space-x-3">
                  <Play className="w-6 h-6 text-green-400" />
                  <h3 className="text-xl font-semibold text-white">TrackGuard Analysis</h3>
                  {showDetections && (
                    <button
                      onClick={() => setShowDetections(!showDetections)}
                      className={`flex items-center space-x-1 px-3 py-1 rounded-full text-sm font-medium transition-all ${
                        showDetections 
                          ? 'bg-green-500/20 text-green-400 border border-green-500/30'
                          : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                      }`}
                    >
                      <Eye className="w-4 h-4" />
                      <span>Detections</span>
                    </button>
                  )}
                </div>
                <button
                  onClick={clearVideo}
                  className="p-2 hover:bg-gray-800 rounded-lg transition-colors"
                >
                  <X className="w-5 h-5 text-gray-400" />
                </button>
              </div>
              
              {/* Upload Progress */}
              {isUploading && (
                <div className="mb-4">
                  <div className="flex items-center justify-between text-sm text-gray-300 mb-2">
                    <span>Uploading video...</span>
                    <span>{uploadProgress}%</span>
                  </div>
                  <div className="w-full bg-gray-700 rounded-full h-2">
                    <div 
                      className="bg-green-500 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${uploadProgress}%` }}
                    ></div>
                  </div>
                </div>
              )}

              {/* Processing Status */}
              {isProcessing && (
                <div className="flex items-center justify-center space-x-3 py-6 text-amber-400">
                  <Loader2 className="w-6 h-6 animate-spin" />
                  <span className="font-medium">AI is analyzing the video...</span>
                </div>
              )}
              
              <div className="relative rounded-xl overflow-hidden border-2 border-green-400/30 shadow-lg shadow-green-400/10">
                <video
                  ref={videoRef}
                  src={uploadedVideo}
                  controls
                  className="w-full h-auto max-h-[500px] bg-black"
                  style={{ filter: 'brightness(1.1) contrast(1.05)' }}
                >
                  Your browser does not support the video tag.
                </video>
                
                {/* Detection overlay canvas */}
                {showDetections && (
                  <canvas
                    ref={canvasRef}
                    className="absolute top-0 left-0 w-full h-full pointer-events-none"
                    style={{ maxHeight: '500px' }}
                  />
                )}
                
                {/* Status indicators */}
                <div className="absolute top-4 left-4 flex space-x-2">
                  <div className="bg-green-500/90 backdrop-blur-sm text-white px-3 py-1 rounded-full text-sm font-medium">
                    ACTIVE
                  </div>
                  {isProcessing ? (
                    <div className="bg-amber-500/90 backdrop-blur-sm text-white px-3 py-1 rounded-full text-sm font-medium">
                      ANALYZING
                    </div>
                  ) : showDetections ? (
                    <div className="bg-blue-500/90 backdrop-blur-sm text-white px-3 py-1 rounded-full text-sm font-medium flex items-center space-x-1">
                      <Zap className="w-3 h-3" />
                      <span>AI ACTIVE</span>
                    </div>
                  ) : null}
                </div>

                {/* Risk indicator */}
                {showDetections && detectionResults.length > 0 && (
                  <div className="absolute top-4 right-4">
                    <div className={`bg-black/80 backdrop-blur-sm px-3 py-2 rounded-lg border ${
                      detectionResults[0]?.overall_risk > 0.7 ? 'border-red-500/50' :
                      detectionResults[0]?.overall_risk > 0.4 ? 'border-amber-500/50' :
                      'border-green-500/50'
                    }`}>
                      <div className="text-xs text-gray-300 mb-1">Risk Level</div>
                      <div className={`text-sm font-bold ${getRiskColor(detectionResults[0]?.overall_risk || 0)}`}>
                        {detectionResults[0]?.overall_decision || 'CLEAR'}
                      </div>
                    </div>
                  </div>
                )}
              </div>
              
              <div className="mt-4 space-y-3">
                {/* Analysis Results */}
                {showDetections && detectionResults.length > 0 && (
                  <div className="p-4 bg-gray-800/50 rounded-lg border border-gray-700">
                    <div className="flex items-center space-x-2 mb-2">
                      <CheckCircle className="w-5 h-5 text-green-400" />
                      <p className="text-green-400 font-medium">AI Analysis Complete</p>
                    </div>
                    <p className="text-gray-300 text-sm mb-3">
                      TrackGuard detected {detectionResults.reduce((acc, result) => acc + result.detections.length, 0)} objects across {detectionResults.length} analyzed frames.
                    </p>
                    
                    {/* Detection Summary */}
                    <div className="grid grid-cols-3 gap-4 text-center">
                      <div className="bg-green-500/10 border border-green-500/20 rounded-lg p-3">
                        <div className="text-green-400 font-bold text-lg">
                          {detectionResults.filter(r => r.overall_decision === 'CLEAR').length}
                        </div>
                        <div className="text-green-300 text-xs">Clear Frames</div>
                      </div>
                      <div className="bg-amber-500/10 border border-amber-500/20 rounded-lg p-3">
                        <div className="text-amber-400 font-bold text-lg">
                          {detectionResults.filter(r => ['CAUTION', 'SLOW_DOWN'].includes(r.overall_decision)).length}
                        </div>
                        <div className="text-amber-300 text-xs">Caution Frames</div>
                      </div>
                      <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-3">
                        <div className="text-red-400 font-bold text-lg">
                          {detectionResults.filter(r => r.overall_decision === 'EMERGENCY_BRAKE').length}
                        </div>
                        <div className="text-red-300 text-xs">Critical Frames</div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Default completion message */}
                {!isProcessing && !isUploading && !showDetections && (
                  <div className="p-4 bg-gray-800/50 rounded-lg border border-gray-700">
                    <p className="text-green-400 font-medium mb-1">✓ Video Loaded Successfully</p>
                    <p className="text-gray-300 text-sm">
                      {connectionStatus === 'connected' 
                        ? "TrackGuard AI is ready to analyze your video for potential hazards."
                        : "Demo mode - Upload functionality showcased. Connect to API for full AI analysis."
                      }
                    </p>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </section>
  );
};

export default VideoUpload;