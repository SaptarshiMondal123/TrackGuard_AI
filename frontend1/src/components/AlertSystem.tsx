import React, { useState, useEffect } from 'react';
import { AlertTriangle, CheckCircle, Info, X, Volume2, VolumeX } from 'lucide-react';

interface Alert {
  id: string;
  type: 'INFO' | 'WARNING' | 'CRITICAL' | 'EMERGENCY';
  message: string;
  timestamp: number;
  status: 'active' | 'acknowledged';
  location?: {
    lat: number;
    lng: number;
  };
}

interface AlertSystemProps {
  isVisible?: boolean;
}

const AlertSystem: React.FC<AlertSystemProps> = ({ isVisible = false }) => {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [soundEnabled, setSoundEnabled] = useState(true);
  const [showPanel, setShowPanel] = useState(isVisible);

  // Mock alerts for demonstration
  useEffect(() => {
    const mockAlerts: Alert[] = [
      {
        id: 'alert_1',
        type: 'WARNING',
        message: 'Person detected on track at 150m - Caution advised',
        timestamp: Date.now() - 30000,
        status: 'active',
        location: { lat: 22.5726, lng: 88.3639 }
      },
      {
        id: 'alert_2',
        type: 'CRITICAL',
        message: 'Large vehicle blocking railway crossing ahead',
        timestamp: Date.now() - 60000,
        status: 'active',
        location: { lat: 22.5742, lng: 88.3658 }
      },
      {
        id: 'alert_3',
        type: 'INFO',
        message: 'Track inspection completed - All clear',
        timestamp: Date.now() - 120000,
        status: 'acknowledged',
        location: { lat: 22.5760, lng: 88.3676 }
      }
    ];
    setAlerts(mockAlerts);
  }, []);

  const acknowledgeAlert = (alertId: string) => {
    setAlerts(prev => 
      prev.map(alert => 
        alert.id === alertId 
          ? { ...alert, status: 'acknowledged' }
          : alert
      )
    );
  };

  const dismissAlert = (alertId: string) => {
    setAlerts(prev => prev.filter(alert => alert.id !== alertId));
  };

  const getAlertIcon = (type: Alert['type']) => {
    switch (type) {
      case 'INFO':
        return <Info className="w-5 h-5 text-blue-400" />;
      case 'WARNING':
        return <AlertTriangle className="w-5 h-5 text-amber-400" />;
      case 'CRITICAL':
      case 'EMERGENCY':
        return <AlertTriangle className="w-5 h-5 text-red-400" />;
      default:
        return <Info className="w-5 h-5 text-gray-400" />;
    }
  };

  const getAlertBorderColor = (type: Alert['type']) => {
    switch (type) {
      case 'INFO':
        return 'border-blue-500/30 bg-blue-500/5';
      case 'WARNING':
        return 'border-amber-500/30 bg-amber-500/5';
      case 'CRITICAL':
        return 'border-red-500/30 bg-red-500/5';
      case 'EMERGENCY':
        return 'border-red-600/40 bg-red-600/10 shadow-lg shadow-red-500/20';
      default:
        return 'border-gray-500/30 bg-gray-500/5';
    }
  };

  const formatTimestamp = (timestamp: number) => {
    const now = Date.now();
    const diff = now - timestamp;
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(minutes / 60);
    
    if (hours > 0) return `${hours}h ago`;
    if (minutes > 0) return `${minutes}m ago`;
    return 'Just now';
  };

  const activeAlerts = alerts.filter(alert => alert.status === 'active');
  const criticalAlerts = activeAlerts.filter(alert => ['CRITICAL', 'EMERGENCY'].includes(alert.type));

  if (!showPanel && activeAlerts.length === 0) return null;

  return (
    <>
      {/* Floating Alert Indicators */}
      {!showPanel && activeAlerts.length > 0 && (
        <div className="fixed top-20 right-4 z-40">
          <button
            onClick={() => setShowPanel(true)}
            className={`flex items-center space-x-2 px-4 py-2 rounded-lg shadow-lg transition-all duration-300 hover:scale-105 ${
              criticalAlerts.length > 0 
                ? 'bg-red-600 hover:bg-red-700 animate-pulse' 
                : 'bg-amber-600 hover:bg-amber-700'
            }`}
          >
            <AlertTriangle className="w-5 h-5 text-white" />
            <span className="text-white font-medium">{activeAlerts.length}</span>
          </button>
        </div>
      )}

      {/* Alert Panel */}
      {showPanel && (
        <div className="fixed top-20 right-4 w-96 max-h-[80vh] bg-gray-900/95 backdrop-blur-sm border border-gray-700 rounded-xl shadow-2xl z-50 overflow-hidden">
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b border-gray-700">
            <div className="flex items-center space-x-3">
              <AlertTriangle className="w-6 h-6 text-amber-400" />
              <h3 className="text-lg font-semibold text-white">Safety Alerts</h3>
              {activeAlerts.length > 0 && (
                <span className="bg-red-600 text-white px-2 py-1 rounded-full text-xs font-medium">
                  {activeAlerts.length}
                </span>
              )}
            </div>
            
            <div className="flex items-center space-x-2">
              <button
                onClick={() => setSoundEnabled(!soundEnabled)}
                className="p-2 hover:bg-gray-800 rounded-lg transition-colors"
                title={soundEnabled ? 'Mute alerts' : 'Unmute alerts'}
              >
                {soundEnabled ? (
                  <Volume2 className="w-4 h-4 text-gray-400" />
                ) : (
                  <VolumeX className="w-4 h-4 text-gray-500" />
                )}
              </button>
              
              <button
                onClick={() => setShowPanel(false)}
                className="p-2 hover:bg-gray-800 rounded-lg transition-colors"
              >
                <X className="w-4 h-4 text-gray-400" />
              </button>
            </div>
          </div>

          {/* Alerts List */}
          <div className="max-h-[60vh] overflow-y-auto">
            {alerts.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-12 text-gray-500">
                <CheckCircle className="w-12 h-12 mb-4" />
                <p className="text-sm">No alerts at this time</p>
                <p className="text-xs text-gray-600">All systems operational</p>
              </div>
            ) : (
              <div className="space-y-2 p-4">
                {alerts.map((alert) => (
                  <div
                    key={alert.id}
                    className={`p-4 rounded-lg border transition-all duration-300 ${getAlertBorderColor(alert.type)} ${
                      alert.status === 'acknowledged' ? 'opacity-60' : 'opacity-100'
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex items-start space-x-3 flex-1">
                        {getAlertIcon(alert.type)}
                        <div className="flex-1">
                          <div className="flex items-center space-x-2 mb-1">
                            <span className={`text-xs font-medium px-2 py-1 rounded ${
                              alert.type === 'INFO' ? 'bg-blue-500/20 text-blue-300' :
                              alert.type === 'WARNING' ? 'bg-amber-500/20 text-amber-300' :
                              'bg-red-500/20 text-red-300'
                            }`}>
                              {alert.type}
                            </span>
                            <span className="text-xs text-gray-500">
                              {formatTimestamp(alert.timestamp)}
                            </span>
                          </div>
                          <p className="text-sm text-gray-200 mb-2">
                            {alert.message}
                          </p>
                          {alert.location && (
                            <p className="text-xs text-gray-500">
                              Location: {alert.location.lat.toFixed(4)}, {alert.location.lng.toFixed(4)}
                            </p>
                          )}
                          
                          {alert.status === 'active' && (
                            <div className="flex space-x-2 mt-3">
                              <button
                                onClick={() => acknowledgeAlert(alert.id)}
                                className="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white text-xs rounded transition-colors"
                              >
                                Acknowledge
                              </button>
                              <button
                                onClick={() => dismissAlert(alert.id)}
                                className="px-3 py-1 bg-gray-600 hover:bg-gray-700 text-white text-xs rounded transition-colors"
                              >
                                Dismiss
                              </button>
                            </div>
                          )}
                        </div>
                      </div>
                      
                      {alert.status === 'acknowledged' && (
                        <CheckCircle className="w-4 h-4 text-green-500 ml-2 flex-shrink-0" />
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Quick Stats */}
          {alerts.length > 0 && (
            <div className="border-t border-gray-700 p-4">
              <div className="grid grid-cols-3 gap-2 text-center">
                <div className="bg-blue-500/10 rounded-lg p-2">
                  <div className="text-blue-400 text-sm font-semibold">
                    {alerts.filter(a => a.type === 'INFO').length}
                  </div>
                  <div className="text-xs text-gray-400">Info</div>
                </div>
                <div className="bg-amber-500/10 rounded-lg p-2">
                  <div className="text-amber-400 text-sm font-semibold">
                    {alerts.filter(a => a.type === 'WARNING').length}
                  </div>
                  <div className="text-xs text-gray-400">Warning</div>
                </div>
                <div className="bg-red-500/10 rounded-lg p-2">
                  <div className="text-red-400 text-sm font-semibold">
                    {alerts.filter(a => ['CRITICAL', 'EMERGENCY'].includes(a.type)).length}
                  </div>
                  <div className="text-xs text-gray-400">Critical</div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </>
  );
};

export default AlertSystem;