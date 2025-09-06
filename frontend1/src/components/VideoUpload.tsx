import React, { useState, useRef } from 'react';
import { Upload, Play, X } from 'lucide-react';

const VideoUpload = () => {
  const [uploadedVideo, setUploadedVideo] = useState<string | null>(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = (file: File) => {
    if (file.type.startsWith('video/')) {
      const url = URL.createObjectURL(file);
      setUploadedVideo(url);
    }
  };

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
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
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
              
              <div className="relative rounded-xl overflow-hidden border-2 border-green-400/30 shadow-lg shadow-green-400/10">
                <video
                  src={uploadedVideo}
                  controls
                  className="w-full h-auto max-h-[500px] bg-black"
                  style={{ filter: 'brightness(1.1) contrast(1.05)' }}
                >
                  Your browser does not support the video tag.
                </video>
                
                {/* Overlay indicators */}
                <div className="absolute top-4 left-4 flex space-x-2">
                  <div className="bg-green-500/90 backdrop-blur-sm text-white px-3 py-1 rounded-full text-sm font-medium">
                    ACTIVE
                  </div>
                  <div className="bg-amber-500/90 backdrop-blur-sm text-white px-3 py-1 rounded-full text-sm font-medium">
                    ANALYZING
                  </div>
                </div>
              </div>
              
              <div className="mt-4 p-4 bg-gray-800/50 rounded-lg border border-gray-700">
                <p className="text-green-400 font-medium mb-1">✓ AI Processing Complete</p>
                <p className="text-gray-300 text-sm">
                  TrackGuard has analyzed the video feed and identified potential hazards along the railway corridor.
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </section>
  );
};

export default VideoUpload;