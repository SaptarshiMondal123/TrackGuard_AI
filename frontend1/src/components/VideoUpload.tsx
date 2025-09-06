import React, { useRef, useState, useEffect } from 'react';
import { Upload, Play, X, AlertTriangle, CheckCircle, Loader, Activity } from 'lucide-react';
import { useTrackGuardStore } from '../store/trackguard';
import { trackGuardAPI } from '../services/api';

const VideoUpload = () => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);

  // Get state from store
  const {
    uploadedVideo,
    processingStatus,
    currentFrame,
    detectionResults,
    setUploadedVideo,
    setProcessingStatus,
    addDetectionResult,
    setCurrentFrame,
    clearResults,
    wsConnected,
    setWsConnected
  } = useTrackGuardStore();

  // WebSocket connection
  useEffect(() => {
    let ws: WebSocket | null = null;

    const connectWebSocket = () => {
      ws = trackGuardAPI.createWebSocket(
        (data) => {
          if (data.type === 'status_update') {
            setProcessingStatus({
              status: data.status,
              progress: data.progress,
              message: data.message,
              video_id: data.video_id
            });
          } else if (data.type === 'detection_result') {
            addDetectionResult(data);
          }
        },
        () => {
          setWsConnected(false);
          // Retry connection after 5 seconds
          setTimeout(connectWebSocket, 5000);
        }
      );

      if (ws) {
        ws.onopen = () => setWsConnected(true);
        ws.onclose = () => setWsConnected(false);
      }
    };

    connectWebSocket();

    return () => {
      if (ws) {
        ws.close();
      }
    };
  }, [setWsConnected, setProcessingStatus, addDetectionResult]);

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
    const files = e.dataTransfer.files;
    if (files && files.length > 0) {
      handleFileSelect(files[0]);
    }
  };

  const handleFileSelect = async (file: File) => {
    if (!file.type.startsWith('video/')) {
      alert('Please select a video file');
      return;
    }

    // Create local URL for preview
    const url = URL.createObjectURL(file);
    setUploadedVideo(url);
    
    // Set uploading status
    setProcessingStatus({
      status: 'uploading',
      progress: 0,
      message: 'Uploading video to TrackGuard AI...'
    });

    try {
      // Upload to backend
      const response = await trackGuardAPI.uploadVideo(file);
      
      setProcessingStatus({
        status: 'processing',
        progress: 0,
        message: 'AI analysis in progress...',
        video_id: response.video_id
      });

    } catch (error) {
      console.error('Upload failed:', error);
      setProcessingStatus({
        status: 'error',
        progress: 0,
        message: 'Upload failed. Please try again.'
      });
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
    clearResults();
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  // Draw detection overlay on canvas
  const drawDetectionOverlay = () => {
    if (!canvasRef.current || !videoRef.current || !currentFrame) return;
    
    const canvas = canvasRef.current;
    const video = videoRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Set canvas size to match video
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    
    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // Draw detections
    currentFrame.detections.forEach((detection) => {
      const [x1, y1, x2, y2] = detection.bbox;
      const width = x2 - x1;
      const height = y2 - y1;
      
      // Color based on decision
      let color = '#10B981'; // Green for CLEAR
      if (detection.decision === 'EMERGENCY_BRAKE') {
        color = '#EF4444'; // Red
      } else if (detection.decision === 'CAUTION') {
        color = '#F59E0B'; // Amber
      } else if (detection.decision === 'SLOW_DOWN') {
        color = '#F97316'; // Orange
      }
      
      // Draw bounding box
      ctx.strokeStyle = color;
      ctx.lineWidth = 3;
      ctx.strokeRect(x1, y1, width, height);
      
      // Draw label background
      ctx.fillStyle = color;
      ctx.fillRect(x1, y1 - 30, 200, 25);
      
      // Draw label text
      ctx.fillStyle = 'white';
      ctx.font = '14px Arial';
      ctx.fillText(`${detection.class} ${(detection.confidence * 100).toFixed(0)}% ${detection.decision}`, x1 + 5, y1 - 10);
    });
  };

  // Update overlay when currentFrame changes
  useEffect(() => {
    if (uploadedVideo && processingStatus.status === 'processing') {
      drawDetectionOverlay();
    }
  }, [currentFrame, uploadedVideo, processingStatus.status]);

  const getRiskColor = (risk: number) => {
    if (risk < 0.3) return 'text-green-400';
    if (risk < 0.7) return 'text-yellow-400';
    return 'text-red-400';
  };

  const getDecisionColor = (decision: string) => {
    switch (decision) {
      case 'CLEAR': return 'text-green-400 bg-green-400/10';
      case 'SLOW_DOWN': return 'text-orange-400 bg-orange-400/10';
      case 'CAUTION': return 'text-yellow-400 bg-yellow-400/10';
      case 'EMERGENCY_BRAKE': return 'text-red-400 bg-red-400/10';
      default: return 'text-gray-400 bg-gray-400/10';
    }
  };

  return (
    <section id="demo" className="py-20 bg-gradient-to-b from-black to-gray-900">
      <div className="container mx-auto px-6">
        <div className="text-center mb-12">
          <h2 className="text-4xl md:text-5xl font-bold text-white mb-4">
            See TrackGuard in <span className="text-green-400">Action</span>
          </h2>
          <p className="text-gray-300 text-xl max-w-2xl mx-auto">
            Upload a railway video to experience our AI-powered collision detection system
          </p>
          
          {/* Connection Status */}
          <div className="flex items-center justify-center mt-4 space-x-4">
            <div className={`flex items-center space-x-2 px-3 py-1 rounded-full text-sm ${wsConnected ? 'bg-green-400/10 text-green-400' : 'bg-red-400/10 text-red-400'}`}>
              <Activity className="w-4 h-4" />
              <span>{wsConnected ? 'Connected' : 'Disconnected'}</span>
            </div>
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
                </div>
                <button
                  onClick={clearVideo}
                  className="p-2 hover:bg-gray-800 rounded-lg transition-colors"
                >
                  <X className="w-5 h-5 text-gray-400" />
                </button>
              </div>
              
              {/* Processing Status */}
              <div className="mb-4 p-4 bg-gray-800/50 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-2">
                    {processingStatus.status === 'processing' && <Loader className="w-4 h-4 text-blue-400 animate-spin" />}
                    {processingStatus.status === 'completed' && <CheckCircle className="w-4 h-4 text-green-400" />}
                    {processingStatus.status === 'error' && <AlertTriangle className="w-4 h-4 text-red-400" />}
                    <span className="text-white font-medium">{processingStatus.message}</span>
                  </div>
                  <span className="text-gray-400">{processingStatus.progress.toFixed(1)}%</span>
                </div>
                <div className="w-full bg-gray-700 rounded-full h-2">
                  <div 
                    className="bg-gradient-to-r from-green-500 to-emerald-600 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${processingStatus.progress}%` }}
                  />
                </div>
              </div>
              
              {/* Video Player with Detection Overlay */}
              <div className="relative rounded-xl overflow-hidden border-2 border-green-400/30 shadow-lg shadow-green-400/10">
                <video
                  ref={videoRef}
                  src={uploadedVideo}
                  controls
                  className="w-full h-auto max-h-[500px] bg-black"
                  style={{ filter: 'brightness(1.1) contrast(1.05)' }}
                  onLoadedMetadata={() => {
                    if (canvasRef.current && videoRef.current) {
                      canvasRef.current.width = videoRef.current.videoWidth;
                      canvasRef.current.height = videoRef.current.videoHeight;
                    }
                  }}
                >
                  Your browser does not support the video tag.
                </video>
                
                {/* Detection Overlay Canvas */}
                <canvas
                  ref={canvasRef}
                  className="absolute top-0 left-0 w-full h-full pointer-events-none"
                  style={{ 
                    display: processingStatus.status === 'processing' && currentFrame ? 'block' : 'none' 
                  }}
                />
                
                {/* Real-time Status Indicators */}
                <div className="absolute top-4 left-4 flex space-x-2">
                  <div className="bg-green-500/90 backdrop-blur-sm text-white px-3 py-1 rounded-full text-sm font-medium">
                    {processingStatus.status === 'processing' ? 'ANALYZING' : 'READY'}
                  </div>
                  {currentFrame && (
                    <div className={`backdrop-blur-sm text-white px-3 py-1 rounded-full text-sm font-medium ${getDecisionColor(currentFrame.overall_decision)}`}>
                      {currentFrame.overall_decision}
                    </div>
                  )}
                </div>

                {/* Real-time Metrics */}
                {currentFrame && (
                  <div className="absolute bottom-4 left-4 right-4">
                    <div className="bg-black/70 backdrop-blur-sm rounded-lg p-3 flex justify-between items-center text-white text-sm">
                      <div>
                        <span className="text-gray-300">Frame:</span> {currentFrame.frame_number}
                      </div>
                      <div>
                        <span className="text-gray-300">Speed:</span> {currentFrame.speed_kmph} km/h
                      </div>
                      <div>
                        <span className="text-gray-300">Risk:</span> 
                        <span className={getRiskColor(currentFrame.overall_risk)}> {(currentFrame.overall_risk * 100).toFixed(0)}%</span>
                      </div>
                      <div>
                        <span className="text-gray-300">Detections:</span> {currentFrame.detections.length}
                      </div>
                    </div>
                  </div>
                )}
              </div>
              
              {/* Processing Results */}
              {processingStatus.status === 'completed' && detectionResults.length > 0 && (
                <div className="mt-4 p-4 bg-gray-800/50 rounded-lg border border-gray-700">
                  <div className="flex items-center space-x-2 mb-3">
                    <CheckCircle className="w-5 h-5 text-green-400" />
                    <p className="text-green-400 font-medium">✓ AI Analysis Complete</p>
                  </div>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                    <div>
                      <span className="text-gray-400">Total Frames:</span>
                      <p className="text-white font-medium">{detectionResults.length}</p>
                    </div>
                    <div>
                      <span className="text-gray-400">Total Detections:</span>
                      <p className="text-white font-medium">{detectionResults.reduce((sum, frame) => sum + frame.detections.length, 0)}</p>
                    </div>
                    <div>
                      <span className="text-gray-400">Max Risk:</span>
                      <p className={`font-medium ${getRiskColor(Math.max(...detectionResults.map(r => r.overall_risk)))}`}>
                        {(Math.max(...detectionResults.map(r => r.overall_risk)) * 100).toFixed(0)}%
                      </p>
                    </div>
                    <div>
                      <span className="text-gray-400">Alerts:</span>
                      <p className="text-white font-medium">{detectionResults.reduce((sum, frame) => sum + frame.alerts.length, 0)}</p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </section>
  );
};

export default VideoUpload;