import React, { useState, useEffect } from 'react';
import { BarChart3, TrendingUp, Shield, AlertTriangle, CheckCircle, Clock, Eye, Zap } from 'lucide-react';

interface DashboardProps {
  detectionResults?: any[];
  isVisible?: boolean;
}

interface MetricCard {
  title: string;
  value: string | number;
  change: string;
  trend: 'up' | 'down' | 'neutral';
  icon: React.ReactNode;
  color: string;
}

const Dashboard: React.FC<DashboardProps> = ({ detectionResults = [], isVisible = false }) => {
  const [metrics, setMetrics] = useState<MetricCard[]>([]);
  const [realtimeData, setRealtimeData] = useState({
    currentThreat: 'CLEAR',
    lastDetection: 'No threats detected',
    systemStatus: 'Operational',
    trackingSince: new Date().toLocaleString()
  });

  // Mock analytics data
  useEffect(() => {
    const mockMetrics: MetricCard[] = [
      {
        title: 'Total Detections',
        value: 1247,
        change: '+12.5%',
        trend: 'up',
        icon: <Eye className="w-6 h-6" />,
        color: 'text-blue-400'
      },
      {
        title: 'False Positives',
        value: 23,
        change: '-8.2%',
        trend: 'down',
        icon: <Shield className="w-6 h-6" />,
        color: 'text-green-400'
      },
      {
        title: 'Critical Alerts',
        value: 5,
        change: '+2',
        trend: 'up',
        icon: <AlertTriangle className="w-6 h-6" />,
        color: 'text-red-400'
      },
      {
        title: 'System Uptime',
        value: '99.8%',
        change: '+0.1%',
        trend: 'up',
        icon: <CheckCircle className="w-6 h-6" />,
        color: 'text-emerald-400'
      },
      {
        title: 'Avg Response Time',
        value: '1.2s',
        change: '-0.3s',
        trend: 'down',
        icon: <Clock className="w-6 h-6" />,
        color: 'text-amber-400'
      },
      {
        title: 'Processing Speed',
        value: '30 FPS',
        change: '+5 FPS',
        trend: 'up',
        icon: <Zap className="w-6 h-6" />,
        color: 'text-purple-400'
      }
    ];
    setMetrics(mockMetrics);
  }, []);

  // Update real-time data based on detection results
  useEffect(() => {
    if (detectionResults.length > 0) {
      const latest = detectionResults[detectionResults.length - 1];
      setRealtimeData(prev => ({
        ...prev,
        currentThreat: latest.overall_decision || 'CLEAR',
        lastDetection: latest.detections?.length > 0 
          ? `${latest.detections.length} objects detected`
          : 'No threats detected'
      }));
    }
  }, [detectionResults]);

  if (!isVisible) return null;

  const getTrendIcon = (trend: 'up' | 'down' | 'neutral') => {
    if (trend === 'up') return <TrendingUp className="w-4 h-4 text-green-400" />;
    if (trend === 'down') return <TrendingUp className="w-4 h-4 text-red-400 rotate-180" />;
    return <div className="w-4 h-4" />;
  };

  const getThreatColor = (threat: string) => {
    switch (threat) {
      case 'EMERGENCY_BRAKE':
        return 'text-red-400 bg-red-500/10 border-red-500/30';
      case 'SLOW_DOWN':
        return 'text-amber-400 bg-amber-500/10 border-amber-500/30';
      case 'CAUTION':
        return 'text-yellow-400 bg-yellow-500/10 border-yellow-500/30';
      default:
        return 'text-green-400 bg-green-500/10 border-green-500/30';
    }
  };

  return (
    <div className="fixed bottom-4 left-4 w-80 max-h-[70vh] bg-gray-900/95 backdrop-blur-sm border border-gray-700 rounded-xl shadow-2xl z-40 overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-700">
        <div className="flex items-center space-x-3">
          <BarChart3 className="w-6 h-6 text-blue-400" />
          <h3 className="text-lg font-semibold text-white">Analytics Dashboard</h3>
        </div>
      </div>

      <div className="max-h-[60vh] overflow-y-auto">
        {/* Real-time Status */}
        <div className="p-4 border-b border-gray-800">
          <h4 className="text-sm font-medium text-gray-300 mb-3">Real-time Status</h4>
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs text-gray-400">Current Threat Level:</span>
              <span className={`px-2 py-1 rounded text-xs font-medium border ${getThreatColor(realtimeData.currentThreat)}`}>
                {realtimeData.currentThreat}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-xs text-gray-400">Last Detection:</span>
              <span className="text-xs text-gray-200">{realtimeData.lastDetection}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-xs text-gray-400">System Status:</span>
              <div className="flex items-center space-x-1">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                <span className="text-xs text-green-400">{realtimeData.systemStatus}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Metrics Grid */}
        <div className="p-4 space-y-3">
          <h4 className="text-sm font-medium text-gray-300">Performance Metrics</h4>
          <div className="grid grid-cols-2 gap-3">
            {metrics.map((metric, index) => (
              <div 
                key={index}
                className="bg-gray-800/50 rounded-lg p-3 border border-gray-700 hover:border-gray-600 transition-colors"
              >
                <div className="flex items-center justify-between mb-2">
                  <div className={`${metric.color}`}>
                    {metric.icon}
                  </div>
                  {getTrendIcon(metric.trend)}
                </div>
                <div className="space-y-1">
                  <div className="text-lg font-bold text-white">{metric.value}</div>
                  <div className="text-xs text-gray-400">{metric.title}</div>
                  <div className={`text-xs flex items-center space-x-1 ${
                    metric.trend === 'up' ? 'text-green-400' : 
                    metric.trend === 'down' ? 'text-red-400' : 'text-gray-400'
                  }`}>
                    <span>{metric.change}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Detection History */}
        {detectionResults.length > 0 && (
          <div className="p-4 border-t border-gray-800">
            <h4 className="text-sm font-medium text-gray-300 mb-3">Recent Detections</h4>
            <div className="space-y-2 max-h-32 overflow-y-auto">
              {detectionResults.slice(-5).reverse().map((result, index) => (
                <div key={index} className="flex items-center justify-between text-xs">
                  <span className="text-gray-400">
                    Frame {result.frame_number || index}
                  </span>
                  <div className="flex items-center space-x-2">
                    <span className="text-gray-300">
                      {result.detections?.length || 0} objects
                    </span>
                    <span className={`px-1 py-0.5 rounded ${getThreatColor(result.overall_decision)}`}>
                      {result.overall_decision}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Quick Actions */}
        <div className="p-4 border-t border-gray-800">
          <h4 className="text-sm font-medium text-gray-300 mb-3">Quick Actions</h4>
          <div className="grid grid-cols-2 gap-2">
            <button className="px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs rounded transition-colors">
              Export Report
            </button>
            <button className="px-3 py-2 bg-gray-600 hover:bg-gray-700 text-white text-xs rounded transition-colors">
              View History
            </button>
            <button className="px-3 py-2 bg-green-600 hover:bg-green-700 text-white text-xs rounded transition-colors">
              Test Alert
            </button>
            <button className="px-3 py-2 bg-purple-600 hover:bg-purple-700 text-white text-xs rounded transition-colors">
              Settings
            </button>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="border-t border-gray-700 p-3">
        <div className="text-xs text-gray-500 text-center">
          Tracking since {realtimeData.trackingSince.split(',')[1]}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;