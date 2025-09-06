import { create } from 'zustand';

interface Detection {
  bbox: [number, number, number, number];
  class: string;
  confidence: number;
  distance: number;
  ttc: number;
  risk_score: number;
  decision: string;
}

interface Alert {
  type: 'INFO' | 'WARNING' | 'CRITICAL' | 'EMERGENCY';
  message: string;
  timestamp: number;
}

interface DetectionFrame {
  frame_number: number;
  timestamp: number;
  detections: Detection[];
  overall_decision: string;
  overall_risk: number;
  speed_kmph: number;
  alerts: Alert[];
}

interface AnalyticsSummary {
  total_videos_processed: number;
  total_detections: number;
  average_risk_score: number;
  alerts_today: number;
  system_uptime: number;
}

interface ProcessingStatus {
  status: 'idle' | 'uploading' | 'processing' | 'completed' | 'error';
  progress: number;
  message: string;
  video_id?: string;
}

interface TrackGuardStore {
  // Video processing state
  uploadedVideo: string | null;
  processingStatus: ProcessingStatus;
  detectionResults: DetectionFrame[];
  currentFrame: DetectionFrame | null;
  
  // Analytics
  analytics: AnalyticsSummary | null;
  
  // Alerts
  alerts: Alert[];
  unreadAlerts: number;
  
  // WebSocket connection
  wsConnected: boolean;
  
  // Actions
  setUploadedVideo: (url: string | null) => void;
  setProcessingStatus: (status: ProcessingStatus) => void;
  addDetectionResult: (result: DetectionFrame) => void;
  setCurrentFrame: (frame: DetectionFrame | null) => void;
  setAnalytics: (analytics: AnalyticsSummary) => void;
  addAlert: (alert: Alert) => void;
  markAlertsRead: () => void;
  setWsConnected: (connected: boolean) => void;
  clearResults: () => void;
}

export const useTrackGuardStore = create<TrackGuardStore>((set, get) => ({
  // Initial state
  uploadedVideo: null,
  processingStatus: {
    status: 'idle',
    progress: 0,
    message: 'Ready to analyze railway videos'
  },
  detectionResults: [],
  currentFrame: null,
  analytics: null,
  alerts: [],
  unreadAlerts: 0,
  wsConnected: false,

  // Actions
  setUploadedVideo: (url) => set({ uploadedVideo: url }),
  
  setProcessingStatus: (status) => set({ processingStatus: status }),
  
  addDetectionResult: (result) => set((state) => ({
    detectionResults: [...state.detectionResults, result],
    currentFrame: result
  })),
  
  setCurrentFrame: (frame) => set({ currentFrame: frame }),
  
  setAnalytics: (analytics) => set({ analytics }),
  
  addAlert: (alert) => set((state) => ({
    alerts: [...state.alerts, alert],
    unreadAlerts: state.unreadAlerts + 1
  })),
  
  markAlertsRead: () => set({ unreadAlerts: 0 }),
  
  setWsConnected: (connected) => set({ wsConnected: connected }),
  
  clearResults: () => set({
    uploadedVideo: null,
    processingStatus: {
      status: 'idle',
      progress: 0,
      message: 'Ready to analyze railway videos'
    },
    detectionResults: [],
    currentFrame: null
  })
}));