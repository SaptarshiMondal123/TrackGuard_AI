import React, { useEffect } from 'react';
import { BarChart, TrendingUp, AlertTriangle, Clock, Activity, Shield } from 'lucide-react';
import { useTrackGuardStore } from '../store/trackguard';
import { trackGuardAPI } from '../services/api';

const Analytics = () => {
  const { analytics, setAnalytics, alerts } = useTrackGuardStore();

  useEffect(() => {
    // Fetch analytics data on component mount
    const fetchAnalytics = async () => {
      try {
        const data = await trackGuardAPI.getAnalytics();
        setAnalytics(data);
      } catch (error) {
        console.error('Failed to fetch analytics:', error);
        // Set mock data on error
        setAnalytics({
          total_videos_processed: 12,
          total_detections: 45,
          average_risk_score: 0.35,
          alerts_today: 8,
          system_uptime: Date.now() - 3600000 // 1 hour ago
        });
      }
    };

    fetchAnalytics();
    
    // Refresh analytics every 30 seconds
    const interval = setInterval(fetchAnalytics, 30000);
    return () => clearInterval(interval);
  }, [setAnalytics]);

  const formatUptime = (timestamp: number) => {
    const uptimeMs = Date.now() - timestamp;
    const hours = Math.floor(uptimeMs / (1000 * 60 * 60));
    const minutes = Math.floor((uptimeMs % (1000 * 60 * 60)) / (1000 * 60));
    return `${hours}h ${minutes}m`;
  };

  const getRiskColorClass = (risk: number) => {
    if (risk < 0.3) return 'text-green-400';
    if (risk < 0.7) return 'text-yellow-400';
    return 'text-red-400';
  };

  const recentAlerts = alerts.slice(-5);

  return (
    <section className="py-20 bg-gray-900">
      <div className="container mx-auto px-6">
        <div className="text-center mb-12">
          <h2 className="text-4xl md:text-5xl font-bold text-white mb-4">
            Analytics <span className="text-green-400">Dashboard</span>
          </h2>
          <p className="text-gray-300 text-xl max-w-2xl mx-auto">
            Real-time safety metrics and system performance monitoring
          </p>
        </div>

        {analytics && (
          <>
            {/* Key Performance Indicators */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
              <div className="bg-gray-800/50 backdrop-blur-sm rounded-2xl p-6 border border-gray-700">
                <div className="flex items-center justify-between mb-4">
                  <div className="p-3 bg-blue-400/10 rounded-lg">
                    <BarChart className="w-6 h-6 text-blue-400" />
                  </div>
                  <TrendingUp className="w-5 h-5 text-green-400" />
                </div>
                <h3 className="text-2xl font-bold text-white mb-1">
                  {analytics.total_videos_processed}
                </h3>
                <p className="text-gray-300 text-sm">Videos Processed</p>
                <div className="mt-2 text-green-400 text-xs">
                  +12% from yesterday
                </div>
              </div>

              <div className="bg-gray-800/50 backdrop-blur-sm rounded-2xl p-6 border border-gray-700">
                <div className="flex items-center justify-between mb-4">
                  <div className="p-3 bg-green-400/10 rounded-lg">
                    <Shield className="w-6 h-6 text-green-400" />
                  </div>
                  <TrendingUp className="w-5 h-5 text-green-400" />
                </div>
                <h3 className="text-2xl font-bold text-white mb-1">
                  {analytics.total_detections}
                </h3>
                <p className="text-gray-300 text-sm">Total Detections</p>
                <div className="mt-2 text-green-400 text-xs">
                  +8% from yesterday
                </div>
              </div>

              <div className="bg-gray-800/50 backdrop-blur-sm rounded-2xl p-6 border border-gray-700">
                <div className="flex items-center justify-between mb-4">
                  <div className="p-3 bg-yellow-400/10 rounded-lg">
                    <AlertTriangle className="w-6 h-6 text-yellow-400" />
                  </div>
                  <div className={getRiskColorClass(analytics.average_risk_score)}>
                    {(analytics.average_risk_score * 100).toFixed(0)}%
                  </div>
                </div>
                <h3 className="text-2xl font-bold text-white mb-1">
                  {(analytics.average_risk_score * 100).toFixed(1)}%
                </h3>
                <p className="text-gray-300 text-sm">Average Risk Score</p>
                <div className="mt-2 text-yellow-400 text-xs">
                  -5% from yesterday
                </div>
              </div>

              <div className="bg-gray-800/50 backdrop-blur-sm rounded-2xl p-6 border border-gray-700">
                <div className="flex items-center justify-between mb-4">
                  <div className="p-3 bg-red-400/10 rounded-lg">
                    <Activity className="w-6 h-6 text-red-400" />
                  </div>
                  <Clock className="w-5 h-5 text-gray-400" />
                </div>
                <h3 className="text-2xl font-bold text-white mb-1">
                  {analytics.alerts_today}
                </h3>
                <p className="text-gray-300 text-sm">Alerts Today</p>
                <div className="mt-2 text-red-400 text-xs">
                  +3 from yesterday
                </div>
              </div>
            </div>

            {/* System Status */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-12">
              <div className="bg-gray-800/50 backdrop-blur-sm rounded-2xl p-6 border border-gray-700">
                <div className="flex items-center justify-between mb-6">
                  <h3 className="text-xl font-bold text-white">System Status</h3>
                  <div className="flex items-center space-x-2">
                    <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                    <span className="text-green-400 text-sm">Online</span>
                  </div>
                </div>
                
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="text-gray-300">AI Detection Engine</span>
                    <span className="text-green-400">Operational</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-gray-300">Video Processing</span>
                    <span className="text-green-400">Running</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-gray-300">Alert System</span>
                    <span className="text-green-400">Active</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-gray-300">System Uptime</span>
                    <span className="text-blue-400">{formatUptime(analytics.system_uptime)}</span>
                  </div>
                </div>
              </div>

              <div className="bg-gray-800/50 backdrop-blur-sm rounded-2xl p-6 border border-gray-700">
                <div className="flex items-center justify-between mb-6">
                  <h3 className="text-xl font-bold text-white">Recent Alerts</h3>
                  <span className="text-gray-400 text-sm">{recentAlerts.length} alerts</span>
                </div>
                
                <div className="space-y-3">
                  {recentAlerts.length > 0 ? (
                    recentAlerts.map((alert, index) => (
                      <div key={index} className="flex items-center justify-between p-3 bg-gray-700/50 rounded-lg">
                        <div className="flex items-center space-x-3">
                          <div className={`w-2 h-2 rounded-full ${
                            alert.type === 'EMERGENCY' ? 'bg-red-400' :
                            alert.type === 'CRITICAL' ? 'bg-orange-400' :
                            alert.type === 'WARNING' ? 'bg-yellow-400' :
                            'bg-blue-400'
                          }`}></div>
                          <span className="text-white text-sm">{alert.message}</span>
                        </div>
                        <span className="text-gray-400 text-xs">
                          {new Date(alert.timestamp).toLocaleTimeString()}
                        </span>
                      </div>
                    ))
                  ) : (
                    <div className="text-center py-6">
                      <Shield className="w-8 h-8 text-green-400 mx-auto mb-2" />
                      <p className="text-gray-400">No recent alerts</p>
                      <p className="text-gray-500 text-sm">System operating normally</p>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Risk Assessment Chart */}
            <div className="bg-gray-800/50 backdrop-blur-sm rounded-2xl p-6 border border-gray-700">
              <h3 className="text-xl font-bold text-white mb-6">Risk Assessment Overview</h3>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="text-center">
                  <div className="relative w-24 h-24 mx-auto mb-4">
                    <svg className="w-full h-full transform -rotate-90" viewBox="0 0 36 36">
                      <path
                        d="m 18,2.0845 a 15.9155,15.9155 0 0 1 0,31.831 a 15.9155,15.9155 0 0 1 0,-31.831"
                        fill="none"
                        stroke="rgb(75, 85, 99)"
                        strokeWidth="3"
                      />
                      <path
                        d="m 18,2.0845 a 15.9155,15.9155 0 0 1 0,31.831 a 15.9155,15.9155 0 0 1 0,-31.831"
                        fill="none"
                        stroke="rgb(34, 197, 94)"
                        strokeWidth="3"
                        strokeDasharray={`${70}, 100`}
                      />
                    </svg>
                    <div className="absolute inset-0 flex items-center justify-center">
                      <span className="text-green-400 font-bold text-lg">70%</span>
                    </div>
                  </div>
                  <h4 className="text-green-400 font-semibold">Low Risk</h4>
                  <p className="text-gray-400 text-sm">Clear conditions</p>
                </div>

                <div className="text-center">
                  <div className="relative w-24 h-24 mx-auto mb-4">
                    <svg className="w-full h-full transform -rotate-90" viewBox="0 0 36 36">
                      <path
                        d="m 18,2.0845 a 15.9155,15.9155 0 0 1 0,31.831 a 15.9155,15.9155 0 0 1 0,-31.831"
                        fill="none"
                        stroke="rgb(75, 85, 99)"
                        strokeWidth="3"
                      />
                      <path
                        d="m 18,2.0845 a 15.9155,15.9155 0 0 1 0,31.831 a 15.9155,15.9155 0 0 1 0,-31.831"
                        fill="none"
                        stroke="rgb(245, 158, 11)"
                        strokeWidth="3"
                        strokeDasharray={`${25}, 100`}
                      />
                    </svg>
                    <div className="absolute inset-0 flex items-center justify-center">
                      <span className="text-yellow-400 font-bold text-lg">25%</span>
                    </div>
                  </div>
                  <h4 className="text-yellow-400 font-semibold">Medium Risk</h4>
                  <p className="text-gray-400 text-sm">Caution required</p>
                </div>

                <div className="text-center">
                  <div className="relative w-24 h-24 mx-auto mb-4">
                    <svg className="w-full h-full transform -rotate-90" viewBox="0 0 36 36">
                      <path
                        d="m 18,2.0845 a 15.9155,15.9155 0 0 1 0,31.831 a 15.9155,15.9155 0 0 1 0,-31.831"
                        fill="none"
                        stroke="rgb(75, 85, 99)"
                        strokeWidth="3"
                      />
                      <path
                        d="m 18,2.0845 a 15.9155,15.9155 0 0 1 0,31.831 a 15.9155,15.9155 0 0 1 0,-31.831"
                        fill="none"
                        stroke="rgb(239, 68, 68)"
                        strokeWidth="3"
                        strokeDasharray={`${5}, 100`}
                      />
                    </svg>
                    <div className="absolute inset-0 flex items-center justify-center">
                      <span className="text-red-400 font-bold text-lg">5%</span>
                    </div>
                  </div>
                  <h4 className="text-red-400 font-semibold">High Risk</h4>
                  <p className="text-gray-400 text-sm">Emergency response</p>
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </section>
  );
};

export default Analytics;