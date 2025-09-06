const API_BASE_URL = 'http://localhost:8000';

export interface UploadResponse {
  video_id: string;
  filename: string;
  status: string;
  message: string;
}

export interface AnalyticsResponse {
  total_videos_processed: number;
  total_detections: number;
  average_risk_score: number;
  alerts_today: number;
  system_uptime: number;
}

export interface VideoResultsResponse {
  video_id: string;
  status: string;
  total_frames: number;
  processed_frames: number;
  detections: any[];
}

class TrackGuardAPI {
  async uploadVideo(file: File): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE_URL}/upload-video/`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`Upload failed: ${response.statusText}`);
    }

    return response.json();
  }

  async getAnalytics(): Promise<AnalyticsResponse> {
    const response = await fetch(`${API_BASE_URL}/analytics/summary`);
    
    if (!response.ok) {
      throw new Error(`Failed to fetch analytics: ${response.statusText}`);
    }

    return response.json();
  }

  async getVideoResults(videoId: string): Promise<VideoResultsResponse> {
    const response = await fetch(`${API_BASE_URL}/video/${videoId}/results`);
    
    if (!response.ok) {
      throw new Error(`Failed to fetch results: ${response.statusText}`);
    }

    return response.json();
  }

  async healthCheck(): Promise<{ status: string; service: string; timestamp: number }> {
    const response = await fetch(`${API_BASE_URL}/health`);
    
    if (!response.ok) {
      throw new Error(`Health check failed: ${response.statusText}`);
    }

    return response.json();
  }

  // WebSocket connection for real-time updates
  createWebSocket(onMessage: (data: any) => void, onError?: (error: Event) => void): WebSocket | null {
    try {
      const ws = new WebSocket(`ws://localhost:8000/ws`);
      
      ws.onopen = () => {
        console.log('WebSocket connected');
        // Send ping to keep connection alive
        setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: 'ping' }));
          }
        }, 30000);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          onMessage(data);
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        if (onError) onError(error);
      };

      ws.onclose = () => {
        console.log('WebSocket disconnected');
      };

      return ws;
    } catch (error) {
      console.error('Failed to create WebSocket:', error);
      return null;
    }
  }
}

export const trackGuardAPI = new TrackGuardAPI();